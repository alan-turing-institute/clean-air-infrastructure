"""
Module for cleanair parsers.
"""
from .model import ModelFitParser, ValidationParser, get_data_config_from_kwargs
from .complex import (
    SatelliteArgumentParser,
    ScootForecastFeatureArgumentParser,
    ScootRoadmapArgumentParser,
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
    "AQEReadingArgumentParser",
    "get_data_config_from_kwargs",
    "LAQNReadingArgumentParser",
    "ModelFitParser",
    "OsHighwayFeatureArgumentParser",
    "SatelliteArgumentParser",
    "ScootForecastFeatureArgumentParser",
    "ScootReadingArgumentParser",
    "ScootReadingFeatureArgumentParser",
    "ScootRoadmapArgumentParser",
    "StaticDatasetArgumentParser",
    "StreetCanyonFeatureArgumentParser",
    "UKMapFeatureArgumentParser",
    "ValidationParser",
]
