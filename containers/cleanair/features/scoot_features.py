"""
Scoot feature extraction
"""
from sqlalchemy import func
from .feature_extractor import FeatureExtractor
from ..databases.tables import OSHighway, ScootRoadForecast, ScootRoadReading
from ..loggers import get_logger, green
from ..mixins import DateRangeMixin


class ScootFeaturesBase(DateRangeMixin, FeatureExtractor):
    """Process SCOOT values into model features"""

    def __init__(self, table_class, value_type, **kwargs):
        # Initialise parent classes
        super().__init__(dynamic=True, **kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.table_class = table_class
        self.value_type = value_type

        # Log an introductory message
        self.logger.info(
            "Constructing features from per-road SCOOT %s between %s and %s",
            self.value_type,
            green(self.start_datetime),
            green(self.end_datetime),
        )
        with self.dbcnxn.open_session() as session:
            self.logger.info(
                "There are %i per-road SCOOT %s in this time range",
                session.query(self.table_class).filter(
                    self.table_class.measurement_start_utc >= self.start_datetime,
                    self.table_class.measurement_start_utc < self.end_datetime,
                ).count(),
                self.value_type,
            )

    @property
    def table(self):
        """Join the geometry column from OSHighway onto the relevant SCOOT table for feature extraction"""
        with self.dbcnxn.open_session() as session:
            return (
                session.query(self.table_class, OSHighway.geom,)
                .join(OSHighway, self.table_class.road_toid == OSHighway.toid)
                .filter(
                    self.table_class.measurement_start_utc >= self.start_datetime,
                    self.table_class.measurement_start_utc < self.end_datetime,
                )
                .subquery()
            )

    @property
    def features(self):
        return {
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


class ScootReadingFeatures(ScootFeaturesBase):
    """Process SCOOT readings into model features"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(table_class=ScootRoadReading, value_type="readings", sources=["aqe", "laqn"], **kwargs)


class ScootForecastFeatures(ScootFeaturesBase):
    """Process SCOOT forecasts into model features"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(table_class=ScootRoadForecast, value_type="forecasts", sources=["satellite", "hexgrid"], **kwargs)
