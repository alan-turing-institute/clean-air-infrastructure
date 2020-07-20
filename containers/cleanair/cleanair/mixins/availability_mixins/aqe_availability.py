"""
Mixin for checking what aqe data is in database and what is missing
"""
from typing import Optional
from datetime import timedelta
from sqlalchemy import func, text, column, String, distinct
from dateutil.parser import isoparse

from ...decorators import db_query
from ...databases.tables import MetaPoint, AQESite, AQEReading
from ...loggers import get_logger
from ...databases.base import Values


ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")


class AQEAvailabilityMixin:
    """Common database queries. Child classes must also inherit from DBWriter"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @db_query
    def get_aqe_open_sites(self, with_location=False):
        """Get open AQE sites

        Args:
            with_location: Return geometry
        """

        with self.dbcnxn.open_session() as session:

            columns = [
                AQESite.point_id,
                AQESite.site_code,
                AQESite.date_opened,
                AQESite.date_closed,
            ]

            if with_location:
                columns = columns + [MetaPoint.location]

            aqe_site_q = session.query(*columns).filter(AQESite.date_closed.is_(None))

            if with_location:
                aqe_site_q = aqe_site_q.join(
                    MetaPoint, MetaPoint.id == AQESite.point_id
                ).filter(MetaPoint.source == "aqe")

            return aqe_site_q

    @db_query
    def get_in_data(self, start_date: str, end_date: Optional[str] = None):

        """Count the number of AQE readings for each open aqe site between start_date and end_data
        """

        with self.dbcnxn.open_session() as session:

            in_data = (
                session.query(
                    AQEReading.site_code,
                    AQEReading.measurement_start_utc,
                    func.count(AQEReading.value).label("n_records"),
                )
                .filter(AQEReading.measurement_start_utc >= start_date,)
                .group_by(AQEReading.measurement_start_utc, AQEReading.site_code)
            )

            if end_date:
                in_data = in_data.filter(AQEReading.measurement_start_utc < end_date)
            return in_data

    @db_query
    def gen_date_range(self, start_date: str, end_date: Optional[str] = None):

        with self.dbcnxn.open_session() as session:

            # Generate expected time series
            if end_date:
                reference_end_date_minus_1h = (
                    isoparse(end_date) - timedelta(hours=1)
                ).isoformat()

                expected_date_times = session.query(
                    func.generate_series(
                        start_date, reference_end_date_minus_1h, ONE_HOUR_INTERVAL,
                    ).label("measurement_start_utc")
                )
            else:
                expected_date_times = session.query(
                    func.generate_series(
                        start_date,
                        func.current_date() - ONE_HOUR_INTERVAL,
                        ONE_HOUR_INTERVAL,
                    ).label("measurement_start_utc")
                )

            return expected_date_times

    @db_query
    def get_aqe_availability(self, start_date: str, end_date: Optional[str] = None):
        """
        Return all the available data aggregated by reference_start_utc
        between reference_start_date and reference_end_date

        Args:
            reference_start_date (str): iso datetime. The first datetime to check data from
            reference_end_date (str): Optional. iso date. The last datetimee to check data from
        """

        in_data_cte = self.get_in_data(start_date, end_date).cte()
        open_sites_sq = self.get_aqe_open_sites(
            with_location=False, output_type="subquery"
        )
        expected_dates = self.gen_date_range(
            start_date, end_date, output_type="subquery"
        )

        with self.dbcnxn.open_session() as session:

            dates = (
                session.query(open_sites_sq.c.site_code, expected_dates)
                .order_by(open_sites_sq.c.site_code)
                .subquery()
            )

            # return session.query(dates)
            return session.query(
                dates,
                in_data_cte.c.n_records.isnot(None).label("has_data"),
                in_data_cte.c.n_records,
            ).join(
                in_data_cte,
                (dates.c.site_code == in_data_cte.c.site_code)
                & (
                    dates.c.measurement_start_utc == in_data_cte.c.measurement_start_utc
                ),
                isouter=True,
            )
            # available_data_q = (
        #         session.query(
        #             dates.c.reference_start_utc,
        #             dates.c.species,
        #             in_data_cte.c.reference_start_utc.isnot(None).label("has_data"),
        #             in_data_cte.c.n_records,
        #             (in_data_cte.c.n_records == 72 * 32).label("expected_n_records"),
        #         )
        #         .select_entity_from(dates)
        #         .join(
        #             in_data_cte,
        #             (in_data_cte.c.reference_start_utc == dates.c.reference_start_utc)
        #             & (in_data_cte.c.species_code == dates.c.species),
        #             isouter=True,
        #         )
        #     )
        # return session.query(open_sites_sq.c.site_code, in_data_cte).join(
        #     in_data_cte, open_sites_sq.c.site_code == in_data_cte.c.site_code
        # )

        # # Create a CTE of counts of data between reference_start_date and reference_end_date
        # in_data = session.query(
        #     AQEReading.site_code,
        #     AQEReading.measurement_start_utc,
        #     func.count(AQEReading.value).label("n_records"),
        # ).group_by(
        #     SatelliteForecast.species_code, SatelliteForecast.reference_start_utc
        # )

        #     in_data = in_data.filter(
        #         SatelliteForecast.reference_start_utc >= reference_start_date
        #     )

        #     if reference_end_date:
        #         in_data = in_data.filter(
        #             SatelliteForecast.reference_start_utc < reference_end_date
        #         )

        #     in_data_cte = in_data.cte("in_data")

        #     # Generate expected time series
        #     if reference_end_date:
        #         reference_end_date_minus_1d = (
        #             isoparse(reference_end_date) - timedelta(hours=1)
        #         ).isoformat()
        #         expected_date_times = session.query(
        #             func.generate_series(
        #                 reference_start_date,
        #                 reference_end_date_minus_1d,
        #                 ONE_DAY_INTERVAL,
        #             ).label("reference_start_utc")
        #         ).subquery()
        #     else:
        #         expected_date_times = session.query(
        #             func.generate_series(
        #                 reference_start_date,
        #                 func.current_date() - ONE_DAY_INTERVAL,
        #                 ONE_DAY_INTERVAL,
        #             ).label("reference_start_utc")
        #         ).subquery()

        #     # Generate expected species
        #     species_sub_q = session.query(
        #         Values(
        #             [column("species", String),],
        #             *[(polutant,) for polutant in species],
        #             alias_name="t2",
        #         )
        #     ).subquery()

        #     dates = session.query(expected_date_times, species_sub_q).subquery()

        #     available_data_q = (
        #         session.query(
        #             dates.c.reference_start_utc,
        #             dates.c.species,
        #             in_data_cte.c.reference_start_utc.isnot(None).label("has_data"),
        #             in_data_cte.c.n_records,
        #             (in_data_cte.c.n_records == 72 * 32).label("expected_n_records"),
        #         )
        #         .select_entity_from(dates)
        #         .join(
        #             in_data_cte,
        #             (in_data_cte.c.reference_start_utc == dates.c.reference_start_utc)
        #             & (in_data_cte.c.species_code == dates.c.species),
        #             isouter=True,
        #         )
        #     )

        #     return available_data_q
