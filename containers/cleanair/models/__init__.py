"""Model fitting classes"""
try:
    from .model_data import ModelData
    MODEL_DATA_FLAG = True
except Exception as ex:
    MODEL_DATA_FLAG = False

from .model_fitting import SVGP
from .model import Model
from .model_svgp import SVGP_TF1


ALL_ARR = [
    "SVGP",
    "SVGP_TF1"
]

if MODEL_DATA_FLAG:
    ALL_ARR = ["ModelData"] + ALL_ARR

__all__ = ALL_ARR
