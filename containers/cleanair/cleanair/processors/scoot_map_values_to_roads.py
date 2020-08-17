"""
Scoot value extrapolations
"""
from typing import Union
import time
from datetime import datetime, timedelta
from dateutil.parser import isoparse
from sqlalchemy import func, column, text
from sqlalchemy.dialects.postgresql import TIMESTAMP

from ..databases import DBWriter
from ..databases.tables import (
    ScootReading,
    ScootForecast,
    ScootRoadForecast,
    ScootRoadReading,
    ScootRoadMatch,
    OSHighway,
)
from ..loggers import duration, get_logger, green
from ..mixins import DateRangeMixin
from ..decorators import db_query
from ..databases.base import Values


ONE_DAY_INTERVAL = text("interval '1 day'")


class ScootPerRoadValueMapperBase(DateRangeMixin, DBWriter):
    """Extrapolate SCOOT values onto roads"""

    def __init__(self, table_per_detector, table_per_road, value_type, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.table_per_detector = table_per_detector
        self.table_per_road = table_per_road
        self.value_type = value_type

        # Log an introductory message
        self.logger.info(
            "Constructing features from SCOOT %s between %s and %s",
            self.value_type,
            green(self.start_datetime),
            green(self.end_datetime),
        )

    @db_query
    def get_road_ids(self):

        with self.dbcnxn.open_session() as session:

            return session.query(OSHighway.toid)

    @db_query
    def get_processed_data(self, start_datetime: str, end_datetime: str):
        """Check what data has been processed"""

        with self.dbcnxn.open_session() as session:

            # return session.query(
            #     self.table_per_road.road_toid, self.table_per_road.measurement_start_utc
            # ).filter(
            #     self.table_per_road.measurement_start_utc >= start_datetime,
            #     self.table_per_road.measurement_start_utc < end_datetime,
            #     self.table_per_road.road_toid == road_id,
            # )

            expected_date_times = session.query(
                func.generate_series(
                    start_datetime,
                    (isoparse(end_datetime) - timedelta(days=1)).isoformat(),
                    ONE_DAY_INTERVAL,
                ).label("measurement_start_utc")
            ).subquery()

            expected_road_map = session.query(
                OSHighway.toid.label("road_toid"),
                expected_date_times.c.measurement_start_utc,
            )

            return expected_road_map

            session.query(self.table_per_road)

    @db_query
    def update_remote_tables(self):
        session_start = time.time()
        with self.dbcnxn.open_session() as session:
            # For each road, combine the per-detector values according to their weight
            self.logger.info(
                "Constructing per-road SCOOT %s from per-detector %s...",
                self.value_type,
                self.value_type,
            )

            road_match_cte = (
                session.query(ScootRoadMatch)
                .order_by(ScootRoadMatch.road_toid)
                .subquery()
            )

            q_per_road_forecasts = (
                session.query(
                    road_match_cte.c.road_toid,
                    self.table_per_detector.measurement_start_utc,
                    (
                        func.sum(
                            self.table_per_detector.n_vehicles_in_interval
                            * road_match_cte.c.weight
                        )
                        / func.sum(road_match_cte.c.weight)
                    ).label("n_vehicles_in_interval"),
                    (
                        func.sum(
                            self.table_per_detector.occupancy_percentage
                            * road_match_cte.c.weight
                        )
                        / func.sum(road_match_cte.c.weight)
                    ).label("occupancy_percentage"),
                    (
                        func.sum(
                            self.table_per_detector.congestion_percentage
                            * road_match_cte.c.weight
                        )
                        / func.sum(road_match_cte.c.weight)
                    ).label("congestion_percentage"),
                    (
                        func.sum(
                            self.table_per_detector.saturation_percentage
                            * road_match_cte.c.weight
                        )
                        / func.sum(road_match_cte.c.weight)
                    ).label("saturation_percentage"),
                )
                .join(
                    self.table_per_detector,
                    road_match_cte.c.detector_n == self.table_per_detector.detector_id,
                )
                .filter(
                    self.table_per_detector.measurement_start_utc
                    >= self.start_datetime.isoformat(),
                    self.table_per_detector.measurement_start_utc
                    < self.end_datetime.isoformat(),
                )
                .group_by(
                    self.table_per_detector.measurement_start_utc,
                    road_match_cte.c.road_toid,
                )
            )

            return q_per_road_forecasts

            # # Estimate how many records will be updated
            # n_roads = session.query(ScootRoadMatch.road_toid).distinct().count()
            # n_hours = int(
            #     (self.end_datetime - self.start_datetime).total_seconds() / 3600
            # )
            # n_records = n_roads * n_hours
            # self.logger.info(
            #     "Preparing to insert/update approximately %s per-road %s...",
            #     green(n_records),
            #     self.value_type,
            # )

            # # Insert from the query to reduce memory usage and database round-trips
            # # NB. we must overwrite here, as we may be replacing forecasts with readings

            # self.commit_records(
            #     q_per_road_forecasts.subquery(),
            #     table=self.table_per_road,
            #     on_conflict="overwrite",
            # )

            # Print a final timing message
            # self.logger.info(
            #     "Insertion of per-road %s took %s",
            #     self.value_type,
            #     green(duration(session_start, time.time())),
            # )


class ScootPerRoadForecastMapper(ScootPerRoadValueMapperBase):
    """Extrapolate SCOOT forecasts onto roads"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(
            table_per_detector=ScootForecast,
            table_per_road=ScootRoadForecast,
            value_type="forecasts",
            **kwargs,
        )


class ScootPerRoadReadingMapper(ScootPerRoadValueMapperBase):
    """Extrapolate SCOOT readings onto roads"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(
            table_per_detector=ScootReading,
            table_per_road=ScootRoadReading,
            value_type="readings",
            **kwargs,
        )
