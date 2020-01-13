"""Model fitting classes"""
from .model_data import ModelData
from .model_fitting import SVGP
from .model import Model
from .model_svgp import SVGP_TF1

__all__ = [
    "ModelData",
    "SVGP",
    "SVGP_TF1"
]
