"""
Mixin for checking what laqn data is in database and what is missing
"""
from typing import Optional, List
from datetime import timedelta
from sqlalchemy import func, text, column, String, literal
from dateutil.parser import isoparse

from ...decorators import db_query
from ...databases.tables import LAQNSite, LAQNReading
from ...loggers import get_logger
from ...databases.base import Values


ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")


class LAQNAvailabilityMixin:
    """Common database queries. Child classes must also inherit from DBWriter"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @db_query
    def get_laqn_open_sites(self, exclude_closed=True):
        """Get open LAQN sites

        Some LAQN sites have more than one sitecode but have the same location.
        Considers these as one site.
        """

        with self.dbcnxn.open_session() as session:

            columns = [
                LAQNSite.point_id,
                func.array_agg(LAQNSite.site_code).label("site_codes"),
                func.min(LAQNSite.date_opened).label("date_opened"),
                func.max(LAQNSite.date_closed).label("date_closed"),
            ]

            laqn_site_q = session.query(*columns).group_by(LAQNSite.point_id)

            laqn_site_sq = laqn_site_q.order_by(LAQNSite.point_id).subquery()

            if exclude_closed:

                return session.query(laqn_site_sq).filter(
                    laqn_site_sq.c.date_closed.is_(None)
                )

            return session.query(laqn_site_sq)

    @db_query
    def get_raw_data(
        self, species: List[str], start_date: str, end_date: Optional[str] = None,
    ):

        """Get raw LAQN sensor data between a start_date and end_date for a particular species
        """

        with self.dbcnxn.open_session() as session:

            in_data = (
                session.query(
                    LAQNSite.point_id,
                    LAQNReading.species_code,
                    LAQNReading.measurement_start_utc,
                    LAQNReading.value,
                )
                .join(LAQNSite, LAQNReading.site_code == LAQNSite.site_code)
                .filter(
                    LAQNReading.measurement_start_utc >= start_date,
                    LAQNReading.species_code.in_(species),
                    LAQNReading.value.isnot(None),
                )
            )

            if end_date:
                in_data = in_data.filter(LAQNReading.measurement_start_utc < end_date)

            return in_data.order_by(
                LAQNSite.point_id,
                LAQNReading.species_code,
                LAQNReading.measurement_start_utc,
            )

    @db_query
    def gen_date_range(
        self, species: List[str], start_date: str, end_date: Optional[str] = None
    ):
        "Generate a data range and cross join with species"
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

            # Generate expected species
            species_sub_q = session.query(
                Values(
                    [column("species_code", String),],
                    *[(polutant,) for polutant in species],
                    alias_name="t2",
                )
            ).subquery()

            return session.query(expected_date_times.subquery(), species_sub_q)

    @db_query
    def get_laqn_availability(
        self, species: List[str], start_date: str, end_date: Optional[str] = None
    ):
        """
        Return all the available data aggregated by reference_start_utc
        between reference_start_date and reference_end_date

        Args:
            reference_start_date (str): iso datetime. The first datetime to check data from
            reference_end_date (str): Optional. iso date. The last datetimee to check data from
        """

        in_data_cte = self.get_raw_data(species, start_date, end_date).cte()

        open_sites_sq = self.get_laqn_open_sites(output_type="subquery")
        expected_dates = self.gen_date_range(
            species, start_date, end_date, output_type="subquery"
        )

        with self.dbcnxn.open_session() as session:

            dates = session.query(open_sites_sq.c.point_id, expected_dates).subquery()

            return (
                session.query(
                    dates.c.point_id,
                    dates.c.species_code,
                    dates.c.measurement_start_utc,
                    in_data_cte.c.value,
                    in_data_cte.c.value.isnot(None).label("has_data"),
                )
                .join(
                    in_data_cte,
                    (dates.c.point_id == in_data_cte.c.point_id)
                    & (dates.c.species_code == in_data_cte.c.species_code)
                    & (
                        dates.c.measurement_start_utc
                        == in_data_cte.c.measurement_start_utc
                    ),
                    isouter=True,
                )
                .order_by(
                    dates.c.point_id,
                    dates.c.species_code,
                    dates.c.measurement_start_utc,
                )
            )

    @db_query
    def get_laqn_availability_daily(
        self, species: List[str], start_date: str, end_date: Optional[str] = None
    ):
        """
        Return counts of available laqn data by day
        """

        hourly_laqn_avail = self.get_laqn_availability(
            species, start_date, end_date, output_type="subquery"
        )

        with self.dbcnxn.open_session() as session:

            return session.query(
                hourly_laqn_avail.c.point_id,
                hourly_laqn_avail.c.species_code,
                func.date_trunc("day", hourly_laqn_avail.c.measurement_start_utc).label(
                    "date"
                ),
                func.count(hourly_laqn_avail.c.value).label("n_readings"),
                literal(24).label("expected_readings"),
                (func.count(hourly_laqn_avail.c.value) != 0).label("has_data"),
                (func.count(hourly_laqn_avail.c.value) == 24).label("full_data"),
            ).group_by(
                hourly_laqn_avail.c.point_id,
                func.date_trunc("day", hourly_laqn_avail.c.measurement_start_utc).label(
                    "date"
                ),
                hourly_laqn_avail.c.species_code,
            )

    # pylint: disable=C0103
    @db_query
    def get_laqn_availability_daily_total(
        self, species: List[str], start_date: str, end_date: Optional[str] = None
    ):
        """
        Return counts of available laqn data by day
        """

        daily_laqn_avail = self.get_laqn_availability_daily(
            species, start_date, end_date, output_type="subquery"
        )

        with self.dbcnxn.open_session() as session:

            return (
                session.query(
                    daily_laqn_avail.c.date,
                    daily_laqn_avail.c.species_code,
                    func.count(daily_laqn_avail.c.has_data)
                    .filter(daily_laqn_avail.c.has_data)
                    .label("total_some_data"),
                    func.count(daily_laqn_avail.c.full_data)
                    .filter(daily_laqn_avail.c.full_data)
                    .label("total_full_data"),
                    func.count(daily_laqn_avail.c.date).label("total"),
                )
                .group_by(daily_laqn_avail.c.date, daily_laqn_avail.c.species_code,)
                .order_by(daily_laqn_avail.c.species_code, daily_laqn_avail.c.date)
            )
