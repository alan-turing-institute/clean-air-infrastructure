"""Model fitting classes"""
from .model import ModelMixin
from .model_data import ModelData, ModelDataExtractor
from .model_config import ModelConfig

# from .svgp import SVGP
# from .mr_dgp_model import MRDGP

from .schemas import (
    StaticFeatureSchema,
    DynamicFeatureSchema,
    StaticFeatureLocSchema,
    StaticFeatureTimeSpecies,
    StaticFeaturesWithSensors,
)

__all__ = [
    "ModelConfig",
    "ModelMixin",
    "ModelData",
    "ModelDataExtractor",
    # "SVGP",
    # "MRDGP",
    "StaticFeatureSchema",
    "DynamicFeatureSchema",
    "StaticFeatureLocSchema",
    "StaticFeatureTimeSpecies",
    "StaticFeaturesWithSensors",
]
