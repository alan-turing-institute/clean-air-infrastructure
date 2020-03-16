"""
Module for interacting with tables in the Azure Postgres database
"""
from .aqe_tables import AQESite, AQEReading
from .features_tables import StaticFeature, DynamicFeature
from .hexgrid_table import HexGrid
from .laqn_tables import LAQNSite, LAQNReading
from .londonboundary_table import LondonBoundary
from .meta_point_table import MetaPoint
from .oshighway_table import OSHighway
from .rectgrid_table import RectGrid, RectGrid100
from .ukmap_tables import UKMap
from .street_canyon_tables import StreetCanyon
from .data_config_table import DataConfig
from .model_table import ModelTable
from .instance_table import InstanceTable
from .result_table import ResultTable

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
    ScootRoadReading,
    ScootRoadMatch,
)


__all__ = [
    "AQEReading",
    "AQESite",
    "DataConfig",
    "DynamicFeature",
    "HexGrid",
    "LAQNReading",
    "LAQNSite",
    "LondonBoundary",
    "MetaPoint",
    "ModelTable",
    "OSHighway",
    "RectGrid",
    "RectGrid100",
    "ResultTable",
    "SatelliteDiscreteSite",
    "SatelliteForecastReading",
    "SatelliteSite",
    "ScootDetector",
    "ScootForecast",
    "ScootReading",
    "ScootRoadForecast",
    "ScootRoadMatch",
    "ScootRoadReading",
    "StaticFeature",
    "StreetCanyon",
    "UKMap",
]
