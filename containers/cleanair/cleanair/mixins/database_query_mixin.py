"""
Mixin for useful database queries
"""
from datetime import datetime
from typing import List, Tuple
import pandas as pd
from sqlalchemy import and_, or_, func, literal, null
from ..decorators import db_query
from ..databases.tables import (
    AQEReading,
    AQESite,
    StaticFeature,
    DynamicFeature,
    LAQNReading,
    LAQNSite,
    LondonBoundary,
    MetaPoint,
    SatelliteForecast,
    ScootDetector,
    ScootReading,
)
from ..loggers import get_logger
from ..timestamps import as_datetime


class DBQueryMixin:
    """Common database queries. Child classes must also inherit from DBWriter"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London"""
        with self.dbcnxn.open_session() as session:
            hull = session.scalar(
                func.ST_ConvexHull(func.ST_Collect(LondonBoundary.geom))
            )
        return hull

    @db_query
    def get_available_static_features(self):
        """Return available static features from the CleanAir database
        """

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(StaticFeature.feature_name).distinct(
                StaticFeature.feature_name
            )

            return feature_types_q

    @db_query
    def get_available_dynamic_features(self, start_date, end_date):
        """Return a list of the available dynamic features in the database.
            Only returns features that are available between start_date and end_date
        """

        with self.dbcnxn.open_session() as session:

            available_dynamic_sq = (
                session.query(
                    DynamicFeature.feature_name,
                    func.min(DynamicFeature.measurement_start_utc).label("min_date"),
                    func.max(DynamicFeature.measurement_start_utc).label("max_date"),
                )
                .group_by(DynamicFeature.feature_name)
                .subquery()
            )

            available_dynamic_q = session.query(available_dynamic_sq).filter(
                and_(
                    available_dynamic_sq.c["min_date"] <= start_date,
                    available_dynamic_sq.c["max_date"] >= end_date,
                )
            )

            return available_dynamic_q

    @db_query
    def get_available_sources(self):
        """Return the available interest point sources in a database"""

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(MetaPoint.source).distinct(MetaPoint.source)

            return feature_types_q

    @db_query
    def get_available_interest_points(self, sources, point_ids=None):
        """Return the available interest points for a list of sources, excluding any LAQN or AQE sites that are closed.
        Only returns points withing the London boundary
        Satellite returns features outside of london boundary, while laqn and aqe do not.
        args:
            sources: A list of sources to include
            point_ids: A list of point_ids to include. Default of None returns all points
        """

        bounded_geom = self.query_london_boundary()
        base_query_columns = [
            MetaPoint.id.label("point_id"),
            MetaPoint.source.label("source"),
            MetaPoint.location.label("location"),
            MetaPoint.location.ST_Within(bounded_geom).label("in_london"),
            func.ST_X(MetaPoint.location).label("lon"),
            func.ST_Y(MetaPoint.location).label("lat"),
        ]

        with self.dbcnxn.open_session() as session:

            remaining_sources_q = session.query(
                *base_query_columns,
                null().label("date_opened"),
                null().label("date_closed"),
            ).filter(
                MetaPoint.source.in_(
                    [
                        source
                        for source in sources
                        if source not in ["laqn", "aqe", "satellite"]
                    ]
                ),
                MetaPoint.location.ST_Within(bounded_geom),
            )

            # Satellite is not filtered by london boundary
            sat_sources_q = session.query(
                *base_query_columns,
                null().label("date_opened"),
                null().label("date_closed"),
            ).filter(MetaPoint.source.in_(["satellite"]))

            aqe_sources_q = (
                session.query(
                    *base_query_columns,
                    func.min(AQESite.date_opened),
                    func.min(AQESite.date_closed),
                )
                .join(AQESite, isouter=True)
                .group_by(*base_query_columns)
                .filter(
                    MetaPoint.source.in_(["aqe"]),
                    MetaPoint.location.ST_Within(bounded_geom),
                )
            )

            laqn_sources_q = (
                session.query(
                    *base_query_columns,
                    func.min(LAQNSite.date_opened),
                    func.min(LAQNSite.date_closed),
                )
                .join(LAQNSite, isouter=True)
                .group_by(*base_query_columns)
                .filter(
                    MetaPoint.source.in_(["laqn"]),
                    MetaPoint.location.ST_Within(bounded_geom),
                )
            )

            if ("satellite" in sources) and (len(sources) != 1):
                raise ValueError(
                    """Satellite can only be requested on a source on its own.
                    Ensure 'sources' contains no other options"""
                )
            if sources[0] == "satellite":
                all_sources_sq = remaining_sources_q.union(sat_sources_q).subquery()
            else:
                all_sources_sq = remaining_sources_q.union(
                    aqe_sources_q, laqn_sources_q
                ).subquery()

            # Remove any sources where there is a closing date and filter by point_ids
            all_sources_q = session.query(all_sources_sq).filter(
                all_sources_sq.c.date_closed.is_(None)
            )

            if point_ids:
                all_sources_q = all_sources_q.filter(
                    all_sources_sq.c.point_id.in_(point_ids)
                )

        return all_sources_q

    @db_query
    def get_laqn_readings(self, start_date, end_date):
        """Get LAQN readings from database"""
        with self.dbcnxn.open_session() as session:
            laqn_reading_q = session.query(
                LAQNReading.measurement_start_utc,
                LAQNReading.species_code,
                LAQNReading.value,
                LAQNSite.point_id,
                literal("laqn").label("source"),
            ).join(LAQNSite)
            laqn_reading_q = laqn_reading_q.filter(
                LAQNReading.measurement_start_utc >= start_date,
                LAQNReading.measurement_start_utc < end_date,
            )
            return laqn_reading_q

    @db_query
    def get_aqe_readings(self, start_date, end_date):
        """Get AQE readings from database"""
        with self.dbcnxn.open_session() as session:
            aqe_reading_q = session.query(
                AQEReading.measurement_start_utc,
                AQEReading.species_code,
                AQEReading.value,
                AQESite.point_id,
                literal("aqe").label("source"),
            ).join(AQESite)
            aqe_reading_q = aqe_reading_q.filter(
                AQEReading.measurement_start_utc >= start_date,
                AQEReading.measurement_start_utc < end_date,
            )
            return aqe_reading_q

    @db_query
    def get_satellite_readings_training(self, start_date, end_date, species):
        """Get Satellite data for the training period
           As we get 72 hours of Satellite forecast on each day,
           here we only get Satellite data where the reference date
           is the same as the forecast time.
           i.e. Get data between start_datetime and end_datetime which
           consists of the first 24 hours of forecasts on each of those days
        """

        with self.dbcnxn.open_session() as session:

            sat_q = session.query(SatelliteForecast).filter(
                SatelliteForecast.measurement_start_utc >= start_date,
                SatelliteForecast.measurement_start_utc < end_date,
                func.date(SatelliteForecast.measurement_start_utc)
                == func.date(SatelliteForecast.reference_start_utc),
                SatelliteForecast.species_code.in_(species),
            )

            return sat_q

    @db_query
    def get_satellite_readings_pred(self, start_date, end_date, species):
        """Get Satellite data for the prediction period
           Gets up to 72 hours of predicted data from the satellite readings
           from the same reference_start_utc date as start_date
        """

        if (
            int(
                (as_datetime(end_date) - as_datetime(start_date)).total_seconds()
                // 60
                // 60
            )
            > 72
        ):
            raise ValueError(
                "You may only request forecast data up to 72 hours from start_date"
            )

        with self.dbcnxn.open_session() as session:
            return session.query(SatelliteForecast).filter(
                SatelliteForecast.measurement_start_utc >= start_date,
                SatelliteForecast.measurement_start_utc < end_date,
                func.date(SatelliteForecast.reference_start_utc)
                == as_datetime(start_date).date().isoformat(),
                SatelliteForecast.species_code.in_(species),
            )


class ScootQueryMixin:
    """Queries for the scoot dataset."""

    @db_query
    def get_scoot_with_location(self, start_time, end_time=None, detectors=None):
        """
        Get scoot data with lat and long positions.

        Parameters
        ___

        start_time : str
            Start datetime.

        end_time : str, optional
            End datetime (exclusive).

        detectors : list, optional
            Subset of detectors to get readings for.
        """

        with self.dbcnxn.open_session() as session:
            scoot_readings = (
                session.query(
                    ScootReading.detector_id,
                    func.ST_X(MetaPoint.location).label("lon"),
                    func.ST_Y(MetaPoint.location).label("lat"),
                    ScootReading.measurement_start_utc,
                    ScootReading.measurement_end_utc,
                    ScootReading.n_vehicles_in_interval,
                )
                .join(
                    ScootDetector, ScootReading.detector_id == ScootDetector.detector_n
                )
                .join(MetaPoint, MetaPoint.id == ScootDetector.point_id)
                .filter(ScootReading.measurement_start_utc >= start_time)
            )
            # get readings upto but not including end_time
            if end_time:

                scoot_readings = scoot_readings.filter(
                    ScootReading.measurement_start_utc < end_time
                )
            # get subset of detectors
            if detectors:
                scoot_readings = scoot_readings.filter(
                    ScootReading.detector_id.in_(detectors)
                )

            return scoot_readings
    
    @staticmethod
    def create_day_of_week_daterange(day_of_week: int, start_date: str, end_date: str) -> List[Tuple[str, str]]:
        """Create a list of tuples (start date, end date) where each start_date is the same day of the week.

        Args:
            day_of_week: Day of the week. 0=Mon, 1=Tue, etc.
            start_date: ISO formatted date. All dates in returned list will be at least this date.
            end_date: ISO formatted date. All dates in the returned list will be at most this date.

        Returns
            List of date tuples. The first item in the tuple will be exactly one day before the last item in the tuple.
        """
        # TODO add testing to this function
        # get list of start times that match the weekday within the timerange
        starts = pd.date_range(start_date, end_date).to_series()
        starts = (
            starts[(starts.dt.dayofweek == day_of_week) & (starts < end_date)]
            .dt.strftime("%Y-%m-%d")
            .to_list()
        )

        # get list of end times that match the weekday within the timerange
        ends = pd.date_range(start_date, end_date).to_series()
        ends = (
            ends[(ends.dt.dayofweek == (day_of_week + 1) % 7) & (ends > start_date)]
            .dt.strftime("%Y-%m-%d")
            .to_list()
        )

        return zip(starts, ends)

    @db_query
    def get_scoot_by_dow(self, day_of_week: int, start_time: str, end_time: str = None, detectors: List = None):
        """
        Get scoot readings for days between start_time and end_time filtered by day_of_week.

        Args:
            day_of_week: Day of the week. 0=Mon, 1=Tue, etc.
            start_time: Start datetime.
            end_time: End datetime (exclusive).
            detectors: Subset of detectors to get readings for.
        """
        if not end_time:
            end_time = datetime.now().strftime("%Y-%m-%d")


        with self.dbcnxn.open_session() as session:
            scoot_readings = (
                session.query(
                    ScootReading.detector_id,
                    func.ST_X(MetaPoint.location).label("lon"),
                    func.ST_Y(MetaPoint.location).label("lat"),
                    ScootReading.measurement_start_utc,
                    ScootReading.measurement_end_utc,
                    ScootReading.n_vehicles_in_interval,
                )
                .join(
                    ScootDetector, ScootReading.detector_id == ScootDetector.detector_n
                )
                .join(MetaPoint, MetaPoint.id == ScootDetector.point_id)
            )
            # get a list of or statements
            or_statements = []
            for start, end in self.create_day_of_week_daterange(day_of_week, start_time, end_time):
                # append AND statement
                or_statements.append(
                    and_(
                        ScootReading.measurement_start_utc >= start,
                        ScootReading.measurement_start_utc < end,
                    )
                )
            scoot_readings = scoot_readings.filter(or_(*or_statements))

            # get subset of detectors
            if detectors:
                scoot_readings = scoot_readings.filter(
                    ScootReading.detector_id.in_(detectors)
                )

            return scoot_readings

    @db_query
    def get_scoot_detectors(
        self, offset: int = None, limit: int = None,
    ):
        """
        Get all scoot detectors from the interest point schema.

        Args:
            offset: Start selecting detectors from this integer index.
            limit: Select at most this many detectors.
        """
        with self.dbcnxn.open_session() as session:
            readings = session.query(
                ScootDetector.detector_n.label("detector_id"),
                func.ST_X(MetaPoint.location).label("lon"),
                func.ST_Y(MetaPoint.location).label("lat"),
            ).join(MetaPoint, MetaPoint.id == ScootDetector.point_id)

            if offset and limit:
                readings = readings.order_by(ScootDetector.detector_n).slice(
                    offset, offset + limit
                )

            return readings
