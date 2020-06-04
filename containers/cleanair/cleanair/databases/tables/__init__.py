"""
Module for interacting with tables in the Azure Postgres database
"""
from .air_quality_instance_tables import (
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityMetricsTable,
    AirQualityModelTable,
    AirQualityResultTable,
)
from .aqe_tables import AQESite, AQEReading
from .features_tables import StaticFeature, DynamicFeature
from .hexgrid_table import HexGrid
from .laqn_tables import LAQNSite, LAQNReading
from .londonboundary_table import LondonBoundary
from .meta_point_table import MetaPoint
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
from .urban_village_tables import UrbanVillage
from .gla_scoot_tables import ScootPercentChange
from .jamcam_tables import JamCamFrameStats, JamCamVideoStats

__all__ = [
    "AirQualityDataTable",
    "AirQualityInstanceTable",
    "AirQualityMetricsTable",
    "AirQualityModelTable",
    "AirQualityResultTable",
    "AQEReading",
    "AQESite",
    "DynamicFeature",
    "HexGrid",
    "LAQNReading",
    "LAQNSite",
    "LondonBoundary",
    "JamCamFrameStats",
    "JamCamVideoStats",
    "MetaPoint",
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
    "UrbanVillage",
    "UKMap",
]
