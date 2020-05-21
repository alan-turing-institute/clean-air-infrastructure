"""
Module for cleanair parsers.
"""
from .complex import (
    DataBaseRoleParser,
    DatabaseSetupParser,
    ModelFitParser,
    ModelValidationParser,
    SatelliteArgumentParser,
    ScootReadingArgumentParser,
    ScootForecastFeatureArgumentParser,
)
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
    "StaticDatasetArgumentParser",
    "StreetCanyonFeatureArgumentParser",
    "UKMapFeatureArgumentParser",
]
