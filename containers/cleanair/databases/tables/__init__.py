"""
Module for interacting with tables in the Azure Postgres database
"""
from .aqe_tables import AQESite, AQEReading
from .features_tables import IntersectionGeom, IntersectionValue
from .hexgrid_table import HexGrid
from .laqn_tables import LAQNSite, LAQNReading
from .londonboundary_table import LondonBoundary
from .meta_point_table import MetaPoint
from .oshighway_table import OSHighway
from .rectgrid_table import RectGrid
from .scoot_tables import ScootReading, ScootDetector
from .ukmap_table import UKMap


__all__ = [
    "AQEReading",
    "AQESite",
    "HexGrid",
    "IntersectionGeom",
    "IntersectionValue",
    "LAQNReading",
    "LAQNSite",
    "LondonBoundary",
    "MetaPoint",
    "OSHighway",
    "RectGrid",
    "ScootDetector",
    "ScootReading",
    "UKMap",
]
