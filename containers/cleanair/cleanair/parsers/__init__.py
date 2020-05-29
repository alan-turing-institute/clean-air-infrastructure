"""
Module for cleanair parsers.
"""
from .complex import (
    DataBaseRoleParser,
    DatabaseSetupParser,
    FeatureNameParser,
    ModelFitParser,
    ModelValidationParser,
    OsHighwayFeatureArgumentParser,
    SatelliteArgumentParser,
    ScootReadingArgumentParser,
    ScootForecastFeatureArgumentParser,
    SourceParser,
    FeatureSourceParser,
)
from .simple import (
    AQEReadingArgumentParser,
    LAQNReadingArgumentParser,
    ScootReadingFeatureArgumentParser,
    ScootRoadmapArgumentParser,
    StaticDatasetArgumentParser,
    StreetCanyonFeatureArgumentParser,
    UKMapFeatureArgumentParser,
)

__all__ = [
    "DataBaseRoleParser",
    "DatabaseSetupParser",
    "AQEReadingArgumentParser",
    "LAQNReadingArgumentParser",
    "ModelFitParser",
    "ModelValidationParser",
    "OsHighwayFeatureArgumentParser",
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
