"""
Module for interacting with tables in the Azure Postgres database
"""
from .aqe_tables import AQESite, AQEReading
from .features_tables import IntersectionGeoms, IntersectionValues
from .hexgrid_table import HexGrid
from .interest_point_table import InterestPoint
from .laqn_tables import LAQNSite, LAQNReading
from .londonboundary_table import LondonBoundary
from .rectgrid_table import RectGrid
from .scoot_tables import ScootReading, ScootDetectors
from .ukmap_table import UKMap
from .oshighway_table import OSHighway


__all__ = [
    "AQEReading",
    "AQESite",
    "HexGrid",
    "InterestPoint",
    "LAQNReading",
    "LAQNSite",
    "LondonBoundary",
    "RectGrid",
    "ScootDetectors",
    "ScootReading",
    "UKMap",
    "OSHighway"
    "IntersectionGeoms",
    "IntersectionValues",
]
