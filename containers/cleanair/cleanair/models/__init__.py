"""Model fitting classes"""
from .model import ModelMixin
from .model_data import ModelData
from .model_config import ModelConfig
from .svgp import SVGP
from .mr_dgp_model import MRDGP

__all__ = [
    "ModelConfig",
    "ModelMixin",
    "ModelData",
    "SVGP",
    "MRDGP",
]
