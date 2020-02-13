"""Model fitting classes"""
from .model_data import ModelData
from .model import Model
from .svgp import SVGP_TF1

__all__ = ["ModelData", "SVGP_TF1", "Model"]
