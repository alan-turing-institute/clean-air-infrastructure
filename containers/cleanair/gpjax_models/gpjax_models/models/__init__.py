"""Model fitting classes"""

from ..models.svgp import SVGP
from .stgp_svgp import STGP_SVGP
from .stgp_mrdgp import STGP_MRDGP

__all__ = ["SVGP", "STGP_SVGP", "STGP_MRDGP"]
