"""GLA Scoot lockdown processing"""
import datetime
import logging
import time
import pandas as pd
from sqlalchemy import func
from cleanair.databases import DBWriter
from cleanair.decorators import db_query
from cleanair.databases.tables import (
    ScootReading,
    ScootForecast,
    MetaPoint,
    ScootDetector,
)
from cleanair.decorators import SuppressStdoutStderr
from cleanair.loggers import duration, duration_from_seconds, get_logger, green


class LockdownProcess(DBWriter):
    """Lockdown processing for GLA"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @db_query
    def get_scoot_with_location(self, start_time, end_time=None):
        """
        Get scoot data with lat and long positions
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

            if end_time:

                scoot_readings = scoot_readings.filter(
                    ScootReading.measurement_start_utc < end_time
                )

            return scoot_readings
