"""
Scoot value extrapolations
"""
import time
from sqlalchemy import func
from ..databases import DBWriter
from ..databases.tables import (
    ScootReading,
    ScootForecast,
    ScootRoadForecast,
    ScootRoadReading,
    ScootRoadMatch,
)
from ..loggers import duration, get_logger, green
from ..mixins import DateRangeMixin
from ..decorators import db_query


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
    def update_remote_tables(self):
        session_start = time.time()
        with self.dbcnxn.open_session() as session:
            # For each road, combine the per-detector values according to their weight
            self.logger.info(
                "Constructing per-road SCOOT %s from per-detector %s...",
                self.value_type,
                self.value_type,
            )

            road_match_cte = session.query(ScootRoadMatch).cte("road_match")

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
                    road_match_cte.c.road_toid,
                    self.table_per_detector.measurement_start_utc,
                )
            )

            # Estimate how many records will be updated
            n_roads = session.query(ScootRoadMatch.road_toid).distinct().count()
            n_hours = int(
                (self.end_datetime - self.start_datetime).total_seconds() / 3600
            )
            n_records = n_roads * n_hours
            self.logger.info(
                "Preparing to insert/update approximately %s per-road %s...",
                green(n_records),
                self.value_type,
            )

            # Insert from the query to reduce memory usage and database round-trips
            # NB. we must overwrite here, as we may be replacing forecasts with readings
            with self.dbcnxn.open_session() as session:
                self.commit_records(
                    session,
                    q_per_road_forecasts.subquery(),
                    table=self.table_per_road,
                    on_conflict="overwrite",
                )

            # Print a final timing message
            self.logger.info(
                "Insertion of per-road %s took %s",
                self.value_type,
                green(duration(session_start, time.time())),
            )


class ScootPerRoadForecastMapper(ScootPerRoadValueMapperBase):
    """Extrapolate SCOOT forecasts onto roads"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(
            table_per_detector=ScootForecast,
            table_per_road=ScootRoadForecast,
            value_type="forecasts",
            **kwargs
        )


class ScootPerRoadReadingMapper(ScootPerRoadValueMapperBase):
    """Extrapolate SCOOT readings onto roads"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(
            table_per_detector=ScootReading,
            table_per_road=ScootRoadReading,
            value_type="readings",
            **kwargs
        )
