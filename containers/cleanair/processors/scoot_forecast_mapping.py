"""
Scoot forecast extrapolation
"""
import time
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.inspection import inspect
from ..databases import DBWriter
from ..databases.tables import ScootForecast, ScootRoadForecast, ScootRoadMatch
from ..loggers import duration, get_logger, green
from ..mixins import DateRangeMixin


class ScootForecastMapper(DateRangeMixin, DBWriter):
    """Extrapolate SCOOT forecasts onto roads"""
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Log an introductory message
        self.logger.info("Constructing features from SCOOT forecasts between %s and %s", green(self.start_datetime), green(self.end_datetime))


    def update_remote_tables(self):
        # Log an introductory message
        self.logger.info("Using forecasts between %s and %s", green(self.start_datetime), green(self.end_datetime))

        start_session = time.time()
        with self.dbcnxn.open_session() as session:
            # For each road, combine the per-detector forecasts according to their weight
            self.logger.info("Combining per-detector forecasts into per-road forecasts...")
            q_per_road_forecasts = session.query(
                ScootRoadMatch.road_toid,
                ScootForecast.measurement_start_utc,
                ScootForecast.measurement_end_utc,
                (func.sum(ScootForecast.n_vehicles_in_interval * ScootRoadMatch.weight) / func.sum(ScootRoadMatch.weight)).label("n_vehicles_in_interval"),
                (func.sum(ScootForecast.occupancy_percentage * ScootRoadMatch.weight) / func.sum(ScootRoadMatch.weight)).label("occupancy_percentage"),
                (func.sum(ScootForecast.congestion_percentage * ScootRoadMatch.weight) / func.sum(ScootRoadMatch.weight)).label("congestion_percentage"),
                (func.sum(ScootForecast.saturation_percentage * ScootRoadMatch.weight) / func.sum(ScootRoadMatch.weight)).label("saturation_percentage"),
            ).join(ScootForecast, ScootRoadMatch.detector_n == ScootForecast.detector_id
            ).filter(
                ScootForecast.measurement_start_utc >= self.start_datetime,
                ScootForecast.measurement_end_utc < self.end_datetime,
            ).group_by(
                ScootRoadMatch.road_toid,
                ScootForecast.measurement_start_utc,
                ScootForecast.measurement_end_utc,
            )

            # ... and write back to the forecasts table
            table = ScootRoadForecast.__table__
            column_names = table.columns.keys()
            insert_stmt = insert(ScootRoadForecast).from_select(names=column_names, select=q_per_road_forecasts)
            update_dict = {c.name: c for c in insert_stmt.excluded if not c.primary_key}
            on_duplicate_key_stmt = insert_stmt.on_conflict_do_update(
                index_elements=inspect(table).primary_key, set_=update_dict
            )
            # Commit this to the database
            result = session.execute(on_duplicate_key_stmt)
            self.logger.info("Preparing to insert/update %i per-road forecasts", result.rowcount)
            session.commit()
            self.logger.info(
                "Insertion took %s",
                green(duration(start_session, time.time())),
            )
