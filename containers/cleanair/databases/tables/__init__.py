"""
Module for interacting with tables in the Azure Postgres database
"""
from .aqe_tables import AQESite, AQEReading
from .features_tables import (
    IntersectionGeom,
    IntersectionValue,
    DynamicFeatureValue,
)
from .hexgrid_table import HexGrid
from .laqn_tables import LAQNSite, LAQNReading
from .londonboundary_table import LondonBoundary
from .meta_point_table import MetaPoint
from .model_results_table import ModelResult
from .oshighway_table import OSHighway
from .rectgrid_table import RectGrid, RectGrid100
from .satellite_tables import (
    SatelliteSite,
    SatelliteDiscreteSite,
    SatelliteForecastReading,
)
from .scoot_tables import (
    ScootDetector,
    ScootForecast,
    ScootReading,
    ScootRoadForecast,
    ScootRoadMatch,
)
from .street_canyon_tables import StreetCanyon
from .ukmap_tables import UKMap


__all__ = [
    "AQEReading",
    "AQESite",
    "DynamicFeatureValue",
    "HexGrid",
    "IntersectionGeom",
    "IntersectionValue",
    "LAQNReading",
    "LAQNSite",
    "LondonBoundary",
    "MetaPoint",
    "ModelResult",
    "OSHighway",
    "RectGrid",
    "RectGrid100",
    "SatelliteDiscreteSite",
    "SatelliteForecastReading",
    "SatelliteSite",
    "ScootDetector",
    "ScootForecast",
    "ScootReading",
    "ScootRoadForecast",
    "ScootRoadMatch",
    "StreetCanyon",
    "UKMap",
]
