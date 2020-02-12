"""Model fitting classes"""

try:
    from .model_data import ModelData
    MODEL_DATA_FLAG = True
except Exception as ex:
    MODEL_DATA_FLAG = False

from .model import Model
from .svgp import SVGP_TF1

ALL_ARR = [
    "SVGP_TF1",
    "Model",
]

if MODEL_DATA_FLAG:
    ALL_ARR = ["ModelData"] + ALL_ARR

__all__ = ALL_ARR
