"""Types for the cleanair package."""

from .copernicus_types import Species
from .dataset_types import DataConfig, FeaturesDict, TargetDict
from .model_types import ParamsSVGP

__all__ = ["DataConfig", "FeaturesDict", "TargetDict", "ParamsSVGP", "Species"]
