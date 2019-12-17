"""
Module for interacting with tables in the Azure Postgres database
"""
from .aqe_tables import AQESite, AQEReading
from .features_tables import IntersectionGeom, IntersectionValue, IntersectionValueDynamic
from .hexgrid_table import HexGrid
from .laqn_tables import LAQNSite, LAQNReading
from .londonboundary_table import LondonBoundary
from .meta_point_table import MetaPoint
from .oshighway_table import OSHighway
from .rectgrid_table import RectGrid, RectGrid100
from .scoot_tables import ScootReading, ScootDetector, ScootRoadMatch, ScootRoadUnmatched, ScootRoadReading
from .ukmap_tables import UKMap
from .street_canyon_tables import StreetCanyon
from .model_results_table import ModelResult


__all__ = [
    "AQEReading",
    "AQESite",
    "HexGrid",
    "IntersectionGeom",
    "IntersectionValue",
    "IntersectionValueDynamic",
    "LAQNReading",
    "LAQNSite",
    "LondonBoundary",
    "MetaPoint",
    "OSHighway",
    "RectGrid",
    "RectGrid100",
    "ScootDetector",
    "ScootReading",
    "ScootRoadMatch",
    "ScootRoadUnmatched",
    "ScootRoadReading",
    "UKMap",
    "StreetCanyon",
    "ModelResult",
]
