"""Model fitting classes"""
from .model import ModelMixin
from .model_data import ModelData
from .svgp import SVGP
from .mr_dgp_model import MRDGP

__all__ = [
    "ModelMixin",
    "ModelData",
    "SVGP",
    "MRDGP",
]
