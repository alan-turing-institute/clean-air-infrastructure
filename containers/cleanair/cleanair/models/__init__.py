"""Model fitting classes"""
from .model import Model
from .model_data import ModelData
from .model_config import ModelConfig
from .svgp import SVGP

__all__ = [
    "Model",
    "ModelConfig",
    "ModelData",
    "SVGP",
]
