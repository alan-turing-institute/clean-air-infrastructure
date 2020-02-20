"""
Scoot feature extraction
"""
from sqlalchemy import func
from .features import Features
from ..databases.tables import OSHighway, ScootRoadForecast, ScootRoadReading
from ..loggers import get_logger, green
from ..mixins import DateRangeMixin


SCOOT_FEATURE_DICT = {
    "max_n_vehicles": {
        "type": "value",
        "feature_dict": {"n_vehicles_in_interval": ["*"]},
        "aggfunc": func.max,
    },
    "avg_n_vehicles": {
        "type": "value",
        "feature_dict": {"n_vehicles_in_interval": ["*"]},
        "aggfunc": func.avg,
    },
    "max_occupancy_percentage": {
        "type": "value",
        "feature_dict": {"occupancy_percentage": ["*"]},
        "aggfunc": func.max,
    },
    "avg_occupancy_percentage": {
        "type": "value",
        "feature_dict": {"occupancy_percentage": ["*"]},
        "aggfunc": func.avg,
    },
    "max_congestion_percentage": {
        "type": "value",
        "feature_dict": {"congestion_percentage": ["*"]},
        "aggfunc": func.max,
    },
    "avg_congestion_percentage": {
        "type": "value",
        "feature_dict": {"congestion_percentage": ["*"]},
        "aggfunc": func.avg,
    },
    "max_saturation_percentage": {
        "type": "value",
        "feature_dict": {"saturation_percentage": ["*"]},
        "aggfunc": func.max,
    },
    "avg_saturation_percentage": {
        "type": "value",
        "feature_dict": {"saturation_percentage": ["*"]},
        "aggfunc": func.avg,
    },
}


class ScootReadingFeatures(DateRangeMixin, Features):
    """Process scoot features"""
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(dynamic=True, **kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Log an introductory message
        self.logger.info("Constructing features from SCOOT readings between %s and %s", green(self.start_datetime), green(self.end_datetime))
        with self.dbcnxn.open_session() as session:
            self.logger.info("There are %i readings in this time range", session.query(ScootRoadForecast).count())

    @property
    def table(self):
        """Join the geometry column from OSHighway onto the ScootRoadForecast table for feature extraction"""
        with self.dbcnxn.open_session() as session:
            return (
                session.query(
                    ScootRoadReading,
                    OSHighway.geom,
                )
                .join(OSHighway, ScootRoadReading.road_toid == OSHighway.toid)
                .filter(
                    ScootRoadReading.measurement_start_utc >= self.start_datetime,
                    ScootRoadReading.measurement_start_utc < self.end_datetime,
                )
                .subquery()
            )

    @property
    def features(self):
        return SCOOT_FEATURE_DICT


class ScootForecastFeatures(DateRangeMixin, Features):
    """Process SCOOT forecasts into model features"""
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(dynamic=True, sources=["laqn"], **kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Log an introductory message
        self.logger.info("Constructing features from SCOOT forecasts between %s and %s", green(self.start_datetime), green(self.end_datetime))
        with self.dbcnxn.open_session() as session:
            self.logger.info("There are %i forecasts in this time range", session.query(ScootRoadForecast).count())

    @property
    def table(self):
        """Join the geometry column from OSHighway onto the ScootRoadForecast table for feature extraction"""
        with self.dbcnxn.open_session() as session:
            return (
                session.query(
                    ScootRoadForecast,
                    OSHighway.geom,
                )
                .join(OSHighway, ScootRoadForecast.road_toid == OSHighway.toid)
                .filter(
                    ScootRoadForecast.measurement_start_utc >= self.start_datetime,
                    ScootRoadForecast.measurement_start_utc < self.end_datetime,
                )
                .subquery()
            )

    @property
    def features(self):
        return SCOOT_FEATURE_DICT
