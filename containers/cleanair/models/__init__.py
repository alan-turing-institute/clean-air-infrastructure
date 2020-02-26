"""Model fitting classes"""
from .model_data import ModelData
from .model import Model
from .svgp import SVGP
from .model_withsate import svgp_binnedkernel

__all__ = ["ModelData", "SVGP", "Model","svgp_binnedkernel"]
