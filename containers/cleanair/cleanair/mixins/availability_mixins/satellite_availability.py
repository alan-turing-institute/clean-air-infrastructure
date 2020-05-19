"""
Mixin for checking what satellite data is in database and what is missing
"""
from sqlalchemy import and_, func, literal, null
from ...decorators import db_query
from ...databases.tables import (
    MetaPoint,
    SatelliteForecast,
    SatelliteBox,
    SatelliteGrid,
)
from ...loggers import get_logger
from ...timestamps import as_datetime
from ...decorators import db_query


class SatelliteAvailabilityMixin:
    """Common database queries. Child classes must also inherit from DBWriter"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @db_query
    def get_satellite_interest_points(self):
        """Return all the satellite interest points"""

        with self.dbcnxn.open_session() as session:

            return session.query(MetaPoint).filter(MetaPoint.source == "satellite")

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
            reference_end_date (str): Default None. isostring specifying when to get data from
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
