"""Model fitting classes"""
from .model import Model
from .model_data import ModelData, DataConfig
from .svgp import SVGP, ModelParamSVGP

__all__ = [
    "DataConfig",
    "Model",
    "ModelData",
    "ModelParamSVGP",
    "SVGP",
]
