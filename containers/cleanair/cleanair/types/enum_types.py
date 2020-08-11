"""Cleanair enum types"""
from enum import Enum, unique


@unique
class FeatureNames(str, Enum):
    "Features"
    min_canyon_ratio = "min_canyon_ratio"
    avg_canyon_ratio = "avg_canyon_ratio"
    max_canyon_ratio = "max_canyon_ratio"
    min_canyon_narrowest = "min_canyon_narrowest"
    avg_canyon_narrowest = "avg_canyon_narrowest"
    max_canyon_narrowest = "max_canyon_narrowest"

    total_road_length = "total_road_length"
    total_a_road_primary_length = "total_a_road_primary_length"
    total_a_road_length = "total_a_road_length"
    total_b_road_length = "total_b_road_length"
    total_length = "total_length"

    building_height = "building_height"
    flat = "flat"
    grass = "grass"
    hospitals = "hospitals"
    museums = "museums"
    park = "park"
    water = "water"


@unique
class DynamicFeatureNames(str, Enum):

    max_n_vehicles = "max_n_vehicles"


@unique
class FeatureBufferSize(str, Enum):
    "Buffer sizes"
    one_thousand = 1000
    five_hundred = 500
    two_hundred = 200
    one_hundred = 100
    ten = 10


@unique
class Source(str, Enum):
    """Different types of source for metapoints."""

    aqe = "aqe"
    hexgrid = "hexgrid"
    laqn = "laqn"
    grid_100 = "grid_100"
    scoot = "scoot"
    satellite = "satellite"


@unique
class Species(str, Enum):
    """Valid species for API"""

    # pylint: disable=invalid-name
    NO2 = "NO2"
    PM25 = "PM25"
    PM10 = "PM10"
    O3 = "O3"  # species to get data for

    @classmethod
    def has_key(cls, key: str) -> bool:
        """Returns true if the key is the same as one of the species.

        Args:
            key: The key to check.

        Returns:
            True if key is a species, false otherwise.
        """
        return key in cls.__members__.keys()
