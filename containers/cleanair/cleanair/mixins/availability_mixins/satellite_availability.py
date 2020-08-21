"""
Mixin for checking what satellite data is in database and what is missing
"""
from datetime import timedelta
from sqlalchemy import func, text, column, String
from dateutil.parser import isoparse

from ...decorators import db_query
from ...databases.tables import (
    MetaPoint,
    SatelliteForecast,
    SatelliteBox,
    SatelliteGrid,
)
from ...loggers import get_logger
from ...databases.base import Values


ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")


class SatelliteAvailabilityMixin:
    """Common database queries. Child classes must also inherit from DBWriter"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @db_query
    def get_satellite_box_in_boundary(self):
        "Return box ids that intersect the london boundary"

        london_boundary = self.query_london_boundary(output_type="subquery")

        with self.dbcnxn.open_session() as session:

            box_ids = session.query(SatelliteBox.id, london_boundary.c.geom).filter(
                func.ST_Intersects(london_boundary.c.geom, SatelliteBox.geom)
            )

            return box_ids

    @db_query
    def get_satellite_interest_points_in_boundary(self):
        """Return all the satellite interest points"""

        # ToDo: This returns data from the database. Better to avoid round trips
        boxes_in_london = [
            str(i) for i in self.get_satellite_box_in_boundary(output_type="list")
        ]

        with self.dbcnxn.open_session() as session:

            return session.query(SatelliteGrid.point_id).filter(
                SatelliteGrid.box_id.in_(boxes_in_london)
            )

    @db_query
    def get_satellite_box(self, with_centroids=True):
        """Satellite box geometries over london"""
        with self.dbcnxn.open_session() as session:

            if with_centroids:
                return session.query(
                    SatelliteBox,
                    func.ST_X(SatelliteBox.centroid).label("lon"),
                    func.ST_Y(SatelliteBox.centroid).label("lat"),
                )

            return session.query(SatelliteBox)

    @db_query
    def get_satellite_grid(self):
        """Mapping of satellite interest points to box"""

        with self.dbcnxn.open_session() as session:
            return session.query(SatelliteGrid)

    @db_query
    def get_satellite_forecast(
        self, reference_start_date=None, reference_end_date=None
    ):
        """
        Get satellite forecast readings

        Args:
            reference_start_date (str): Default None. isostring specifying when to get data from.
            reference_end_date (str): Default None. isostring specifying when to get data from.
        """

        with self.dbcnxn.open_session() as session:
            sat_forecast_q = session.query(SatelliteForecast)

            if reference_start_date:
                sat_forecast_q = sat_forecast_q.filter(
                    SatelliteForecast.reference_start_utc >= reference_start_date
                )

            if reference_end_date:
                sat_forecast_q = sat_forecast_q.filter(
                    SatelliteForecast.reference_start_utc < reference_end_date
                )

            return sat_forecast_q

    @db_query
    def get_satellite_availability(
        self, reference_start_date, reference_end_date=None, species=None
    ):
        """
        Return all the available data aggregated by reference_start_utc
        between reference_start_date and reference_end_date

        Args:
            reference_start_date (str): iso date. The first date to check data from
            reference_end_date (str): Optional. iso date. The last date to check data from
            species (list[str]): A list of strings specifying species of polutants
        """

        if not species:
            species = ["NO2", "PM25", "PM10", "O3"]

        with self.dbcnxn.open_session() as session:

            # Create a CTE of counts of data between reference_start_date and reference_end_date
            in_data = session.query(
                SatelliteForecast.species_code,
                SatelliteForecast.reference_start_utc,
                func.count(SatelliteForecast.measurement_start_utc).label("n_records"),
            ).group_by(
                SatelliteForecast.species_code, SatelliteForecast.reference_start_utc
            )

            in_data = in_data.filter(
                SatelliteForecast.reference_start_utc >= reference_start_date
            )

            if reference_end_date:
                in_data = in_data.filter(
                    SatelliteForecast.reference_start_utc < reference_end_date
                )

            in_data_cte = in_data.cte("in_data")

            # Generate expected time series
            if reference_end_date:
                reference_end_date_minus_1d = (
                    isoparse(reference_end_date) - timedelta(hours=1)
                ).isoformat()
                expected_date_times = session.query(
                    func.generate_series(
                        reference_start_date,
                        reference_end_date_minus_1d,
                        ONE_DAY_INTERVAL,
                    ).label("reference_start_utc")
                ).subquery()
            else:
                expected_date_times = session.query(
                    func.generate_series(
                        reference_start_date,
                        func.current_date() - ONE_DAY_INTERVAL,
                        ONE_DAY_INTERVAL,
                    ).label("reference_start_utc")
                ).subquery()

            # Generate expected species
            species_sub_q = session.query(
                Values(
                    [column("species", String),],
                    *[(polutant,) for polutant in species],
                    alias_name="t2",
                )
            ).subquery()

            dates = session.query(expected_date_times, species_sub_q).subquery()

            available_data_q = (
                session.query(
                    dates.c.reference_start_utc,
                    dates.c.species,
                    in_data_cte.c.reference_start_utc.isnot(None).label("has_data"),
                    in_data_cte.c.n_records,
                    (in_data_cte.c.n_records == 72 * 32).label("expected_n_records"),
                )
                .select_entity_from(dates)
                .join(
                    in_data_cte,
                    (in_data_cte.c.reference_start_utc == dates.c.reference_start_utc)
                    & (in_data_cte.c.species_code == dates.c.species),
                    isouter=True,
                )
            )

            return available_data_q
