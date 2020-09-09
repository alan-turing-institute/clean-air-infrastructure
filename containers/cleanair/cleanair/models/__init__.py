"""Model fitting classes"""
from .model import ModelMixin
from .model_data import ModelData
from .model_config import ModelConfig

# from .svgp import SVGP

# ToDO: Reimport SVPG.
__all__ = ["ModelConfig", "ModelMixin", "ModelData"]
