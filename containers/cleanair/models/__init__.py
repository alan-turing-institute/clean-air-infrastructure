"""Model fitting classes"""
from .model_data import ModelData
from .model_fitting import SVGP
from .model_traffic import TrafficForecast

__all__ = [
    "ModelData",
    "SVGP",
    "TrafficForecast",
]
