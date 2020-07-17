"""Model fitting classes"""
from .model import ModelMixin
from .model_data import ModelData
from .svgp import SVGP

__all__ = [
    "ModelMixin",
    "ModelData",
    "SVGP",
]
