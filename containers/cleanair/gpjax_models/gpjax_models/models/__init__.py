"""Model fitting classes"""

from ..models.svgp import SVGP
from .stgp_svgp import STGP_SVGP
from .stgp_mrdgp import STGP_MRDGP
from .vis import SpaceTimeVisualise

__all__ = ["SVGP", "STGP_SVGP", "STGP_MRDGP", "SpaceTimeVisualise"]
