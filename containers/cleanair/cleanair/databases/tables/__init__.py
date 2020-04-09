"""
Module for interacting with tables in the Azure Postgres database
"""
from .aqe_tables import AQESite, AQEReading
from .features_tables import StaticFeature, DynamicFeature
from .hexgrid_table import HexGrid
from .laqn_tables import LAQNSite, LAQNReading
from .londonboundary_table import LondonBoundary
from .meta_point_table import MetaPoint
from .model_results_table import ModelResult
from .oshighway_table import OSHighway
from .rectgrid_table import RectGrid, RectGrid100
from .satellite_tables import (
    SatelliteBox,
    SatelliteGrid,
    SatelliteForecast,
)
from .scoot_tables import (
    ScootDetector,
    ScootForecast,
    ScootReading,
    ScootRoadForecast,
    ScootRoadReading,
    ScootRoadMatch,
)
from .street_canyon_tables import StreetCanyon
from .ukmap_tables import UKMap
from .gla_scoot_tables import ScootPercentChange

__all__ = [
    "AQEReading",
    "AQESite",
    "DynamicFeature",
    "HexGrid",
    "LAQNReading",
    "LAQNSite",
    "LondonBoundary",
    "MetaPoint",
    "ModelResult",
    "OSHighway",
    "RectGrid",
    "RectGrid100",
    "SatelliteGrid",
    "SatelliteForecast",
    "SatelliteBox",
    "ScootDetector",
    "ScootForecast",
    "ScootReading",
    "ScootRoadForecast",
    "ScootRoadMatch",
    "ScootRoadReading",
    "ScootPercentChange",
    "StaticFeature",
    "StreetCanyon",
    "UKMap",
]
