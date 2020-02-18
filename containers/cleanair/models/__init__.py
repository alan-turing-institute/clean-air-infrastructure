"""Model fitting classes"""

try:
    from .model_data import ModelData
    MODEL_DATA_FLAG = True
except Exception as ex:
    MODEL_DATA_FLAG = False

from .model import Model
from .svgp import SVGP
from .mr_dgp_model import MR_DGP_MODEL
from .mr_gprn_model import MR_GPRN_MODEL
from .mr_dgp import MR_DGP

ALL_ARR = [
    "MR_DGP_MODEL",
    "MR_GPRN_MODEL",
    'MR_DGP',
    "SVGP",
    "Model",
]

if MODEL_DATA_FLAG:
    ALL_ARR = ["ModelData"] + ALL_ARR

__all__ = ALL_ARR
