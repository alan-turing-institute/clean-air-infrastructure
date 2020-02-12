"""
Module for interacting with tables in the Azure Postgres database
"""
from .aqe_tables import AQESite, AQEReading
from .features_tables import (
    IntersectionGeom,
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
    ScootDetector,
    ScootForecast,
    ScootReading,
    ScootRoadInverseDistance,
    ScootRoadMatch,
    ScootRoadReading,
    ScootRoadUnmatched,
)
from .ukmap_tables import UKMap
from .street_canyon_tables import StreetCanyon
from .model_results_table import ModelResult
from .satellite_tables import (
    SatelliteSite,
    SatelliteDiscreteSite,
    SatelliteForecastReading,
)


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
    "SatelliteSite",
    "SatelliteDiscreteSite",
    "SatelliteForecastReading",
    "ScootDetector",
    "ScootReading",
    "ScootRoadMatch",
    "ScootRoadUnmatched",
    "ScootRoadReading",
    "ScootRoadInverseDistance",
    "UKMap",
    "StreetCanyon",
    "ModelResult",
]
