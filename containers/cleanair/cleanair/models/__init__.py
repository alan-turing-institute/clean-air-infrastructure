"""Model fitting classes"""
from .model import ModelMixin
from ..dataset.model_data import ModelData, ModelDataExtractor
from ..dataset.model_config import ModelConfig

# from .svgp import SVGP
# from .mr_dgp_model import MRDGP

from ..dataset.schemas import (
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
