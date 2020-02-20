"""
Module for feature extraction
"""
from .scoot_forecast_mapping import ScootForecastMapper
from .scoot_road_mapping import ScootRoadMapper

__all__ = [
    "ScootForecastMapper",
    "ScootRoadMapper",
]
