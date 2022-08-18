"""Model fitting classes"""
from .model import ModelMixin
from cleanair.dataset.model_data import ModelDataExtractor

# from .svgp import SVGP
# from .mr_dgp_model import MRDGP

__all__ = [
    "ModelMixin",
    "ModelDataExtractor",
    # "SVGP",
    # "MRDGP",
]
