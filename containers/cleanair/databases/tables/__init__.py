"""
Module for interacting with tables in the Azure Postgres database
"""
from .aqe_tables import AQESite, AQEReading
from .features_tables import (
    IntersectionValue,
    IntersectionValueDynamic,
)
from .hexgrid_table import HexGrid
from .laqn_tables import LAQNSite, LAQNReading
from .londonboundary_table import LondonBoundary
from .meta_point_table import MetaPoint
from .oshighway_table import OSHighway
from .rectgrid_table import RectGrid, RectGrid100
from .scoot_tables import (
    ScootReading,
    ScootDetector,
    ScootRoadMatch,
    ScootRoadUnmatched,
    ScootRoadReading,
)
from .ukmap_tables import UKMap
from .street_canyon_tables import StreetCanyon
from .data_config_table import DataConfig
from .model_table import ModelTable
from .model_results_table import ModelResult
from .instance_table import InstanceTable
from .result_table import ResultTable
from .satellite_tables import (
    SatelliteSite,
    SatelliteDiscreteSite,
    SatelliteForecastReading,
)


__all__ = [
    "AQEReading",
    "AQESite",
    "DataConfig",
    "HexGrid",
    "IntersectionValue",
    "IntersectionValueDynamic",
    "InstanceTable",
    "LAQNReading",
    "LAQNSite",
    "LondonBoundary",
    "MetaPoint",
    "ModelTable",
    "OSHighway",
    "RectGrid",
    "RectGrid100",
    "ResultTable",
    "SatelliteSite",
    "SatelliteDiscreteSite",
    "SatelliteForecastReading",
    "ScootDetector",
    "ScootReading",
    "ScootRoadMatch",
    "ScootRoadUnmatched",
    "ScootRoadReading",
    "UKMap",
    "StreetCanyon",
    "ModelResult",
]
