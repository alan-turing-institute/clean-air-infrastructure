"""Model fitting classes"""
from .model import Model
from .model_data import ModelData
from .model_traffic import TrafficForecast
from .svgp import SVGP

__all__ = [
    "Model",
    "ModelData",
    "SVGP",
    "TrafficForecast",
]
