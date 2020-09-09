"""Model fitting classes"""
from .model import ModelMixin
from .model_data import ModelData, ModelDataExtractor
from .model_config import ModelConfig

# from .svgp import SVGP


__all__ = ["ModelConfig", "ModelMixin", "ModelData", "ModelDataExtractor"]
