"""
Scoot value extrapolations
"""
import time
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.inspection import inspect
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

    def update_remote_tables(self):
        start_session = time.time()
        with self.dbcnxn.open_session() as session:
            # For each road, combine the per-detector values according to their weight
            self.logger.info(
                "Constructing per-road SCOOT %s from per-detector %s...",
                self.value_type,
                self.value_type,
            )
            q_per_road_forecasts = (
                session.query(
                    ScootRoadMatch.road_toid,
                    self.table_per_detector.measurement_start_utc,
                    self.table_per_detector.measurement_end_utc,
                    (
                        func.sum(
                            self.table_per_detector.n_vehicles_in_interval
                            * ScootRoadMatch.weight
                        )
                        / func.sum(ScootRoadMatch.weight)
                    ).label("n_vehicles_in_interval"),
                    (
                        func.sum(
                            self.table_per_detector.occupancy_percentage
                            * ScootRoadMatch.weight
                        )
                        / func.sum(ScootRoadMatch.weight)
                    ).label("occupancy_percentage"),
                    (
                        func.sum(
                            self.table_per_detector.congestion_percentage
                            * ScootRoadMatch.weight
                        )
                        / func.sum(ScootRoadMatch.weight)
                    ).label("congestion_percentage"),
                    (
                        func.sum(
                            self.table_per_detector.saturation_percentage
                            * ScootRoadMatch.weight
                        )
                        / func.sum(ScootRoadMatch.weight)
                    ).label("saturation_percentage"),
                )
                .join(
                    self.table_per_detector,
                    ScootRoadMatch.detector_n == self.table_per_detector.detector_id,
                )
                .filter(
                    self.table_per_detector.measurement_start_utc
                    >= self.start_datetime,
                    self.table_per_detector.measurement_end_utc < self.end_datetime,
                )
                .group_by(
                    ScootRoadMatch.road_toid,
                    self.table_per_detector.measurement_start_utc,
                    self.table_per_detector.measurement_end_utc,
                )
            )

            # ... and write back to the forecasts table
            table = self.table_per_road.__table__
            column_names = table.columns.keys()
            insert_stmt = insert(self.table_per_road).from_select(
                names=column_names, select=q_per_road_forecasts
            )
            update_dict = {c.name: c for c in insert_stmt.excluded if not c.primary_key}
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_update(
                index_elements=inspect(table).primary_key, set_=update_dict
            )
            # Commit this to the database
            result = session.execute(on_duplicate_key_stmt)
            self.logger.info(
                "Preparing to insert/update %i per-road %s",
                result.rowcount,
                self.value_type,
            )
            session.commit()
            self.logger.info(
                "Insertion took %s", green(duration(start_session, time.time())),
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
