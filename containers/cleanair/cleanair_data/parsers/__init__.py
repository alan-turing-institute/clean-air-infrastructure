"""
Module for cleanair parsers.
"""
from .complex import (
    DataBaseRoleParser,
    DatabaseSetupParser,
    FeatureNameParser,
    SatelliteArgumentParser,
    ScootReadingArgumentParser,
    ScootForecastFeatureArgumentParser,
    FeatureSourceParser,
)
from .dashboard_parser import DashboardParser
from .model_fitting_parser import ModelFittingParser
from .simple import (
    InsertMethodParser,
    WebParser,
    SecretFileParser,
    VerbosityParser,
    DurationParser,
    AQEReadingArgumentParser,
    LAQNReadingArgumentParser,
    ScootReadingFeatureArgumentParser,
    ScootRoadmapArgumentParser,
    SourceParser,
    StaticDatasetArgumentParser,
    StaticFeatureArgumentParser,
    StreetCanyonFeatureArgumentParser,
    UKMapFeatureArgumentParser,
)

__all__ = [
    "DashboardParser",
    "InsertMethodParser",
    "WebParser",
    "SecretFileParser",
    "SourceParser",
    "VerbosityParser",
    "DurationParser",
    "DataBaseRoleParser",
    "DatabaseSetupParser",
    "AQEReadingArgumentParser",
    "LAQNReadingArgumentParser",
    "ModelFittingParser",
    "StaticFeatureArgumentParser",
    "SatelliteArgumentParser",
    "ScootForecastFeatureArgumentParser",
    "ScootReadingArgumentParser",
    "ScootReadingFeatureArgumentParser",
    "ScootRoadmapArgumentParser",
    "SourceParser",
    "FeatureSourceParser",
    "FeatureNameParser",
    "StaticDatasetArgumentParser",
    "StreetCanyonFeatureArgumentParser",
    "UKMapFeatureArgumentParser",
]
