"""
Module for inserting fake data acceptable from the database
"""

from .database_table_fakes import (
    MetaPointSchema,
    LAQNSiteSchema,
    LAQNReadingSchema,
    AQESiteSchema,
    AQEReadingSchema,
    StaticFeaturesSchema,
    AirQualityModelSchema,
    AirQualityDataSchema,
    AirQualityInstanceSchema,
    AirQualityResultSchema,
)


__all__ = [
    "MetaPointSchema",
    "LAQNSiteSchema",
    "LAQNReadingSchema",
    "AQESiteSchema",
    "AQEReadingSchema",
    "StaticFeaturesSchema",
    "AirQualityModelSchema",
    "AirQualityDataSchema",
    "AirQualityInstanceSchema",
    "AirQualityResultSchema",
]
