"""
Module for cleanair parsers.
"""
from .complex import (
    DataBaseRoleParser,
    DatabaseSetupParser,
    SatelliteArgumentParser,
    ScootReadingArgumentParser,
    ScootForecastFeatureArgumentParser,
)
from .dashboard_parser import DashboardParser
from .model_fitting_parser import ModelFittingParser
from .simple import (
    AQEReadingArgumentParser,
    LAQNReadingArgumentParser,
    OsHighwayFeatureArgumentParser,
    ScootReadingFeatureArgumentParser,
    ScootRoadmapArgumentParser,
    StaticDatasetArgumentParser,
    StreetCanyonFeatureArgumentParser,
    UKMapFeatureArgumentParser,
)

__all__ = [
    "DashboardParser",
    "DataBaseRoleParser",
    "DatabaseSetupParser",
    "AQEReadingArgumentParser",
    "LAQNReadingArgumentParser",
    "ModelFittingParser",
    "OsHighwayFeatureArgumentParser",
    "SatelliteArgumentParser",
    "ScootForecastFeatureArgumentParser",
    "ScootReadingArgumentParser",
    "ScootReadingFeatureArgumentParser",
    "ScootRoadmapArgumentParser",
    "StaticDatasetArgumentParser",
    "StreetCanyonFeatureArgumentParser",
    "UKMapFeatureArgumentParser",
]
