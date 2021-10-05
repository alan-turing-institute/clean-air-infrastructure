"""Parameters shared by models."""

from ..types import DynamicFeatureNames, FeatureBufferSize, StaticFeatureNames

LENGTHSCALES: float = 1.0
LIKELIHOOD_VARIANCE: float = 0.1
KERNEL_VARIANCE: float = 1.0
MINIBATCH_SIZE: int = 100

PRODUCTION_DYNAMIC_FEATURES = [
    DynamicFeatureNames.avg_n_vehicles,
]
PRODUCTION_FORECAST_DAYS = 2

PRODUCTION_STATIC_FEATURES = [
    StaticFeatureNames.flat, 
    StaticFeatureNames.max_canyon_ratio,
    StaticFeatureNames.total_a_road_primary_length,
    StaticFeatureNames.total_a_road_length
]
PRODUCTION_BUFFER_SIZES = [FeatureBufferSize.two_hundred]
