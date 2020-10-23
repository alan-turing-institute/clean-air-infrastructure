"""Cleanair enum types"""
from enum import Enum, unique


@unique
class ScootProcessType(str, Enum):
    "Scoot processor type"
    forecast = "forecast"
    real = "real"


class ClusterId(str, Enum):
    """Ids for clusters."""

    laptop = "laptop"
    pearl = "pearl"
    kubernetes = "kubernetes"
    orac = "orac"
    nc6 = "nc6"


@unique
class Tag(str, Enum):
    """Valid options for tags."""

    production = "production"
    test = "test"
    validation = "validation"


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
    "Valid dynamic feature names"
    max_n_vehicles = "max_n_vehicles"
    avg_n_vehicles = "avg_n_vehicles"
    min_n_vehicles = "min_n_vehicles"


@unique
class FeatureBufferSize(str, Enum):
    "Buffer sizes"
    one_thousand = 1000
    five_hundred = 500
    two_hundred = 200
    one_hundred = 100
    ten = 10


@unique
class KernelType(str, Enum):
    """Valid kernels."""

    matern12 = "matern12"
    matern32 = "matern32"
    matern52 = "matern52"
    rbf = "rbf"
    mr_linear = "mr_linear"
    mr_se = "mr_se"


@unique
class ModelName(str, Enum):
    """Valid model names for air quality models."""

    mrdgp = "mrdgp"
    svgp = "svgp"


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


@unique
class Borough(str, Enum):
    """Enum type for boroughs."""

    kingston_upon_thames = "Kingston upon Thames"
    croydon = "Croydon"
    bromley = "Bromley"
    hounslow = "Hounslow"
    ealing = "Ealing"
    havering = "Havering"
    hillingdon = "Hillingdon"
    harrow = "Harrow"
    brent = "Brent"
    barnet = "Barnet"
    lambeth = "Lambeth"
    southwark = "Southwark"
    lewisham = "Lewisham"
    greenwich = "Greenwich"
    bexley = "Bexley"
    enfield = "Enfield"
    waltham_forest = "Waltham Forest"
    redbridge = "Redbridge"
    sutton = "Sutton"
    richmond_upon_thames = "Richmond upon Thames"
    merton = "Merton"
    wandsworth = "Wandsworth"
    hammersmith_and_fulham = "Hammersmith and Fulham"
    kensington_and_chelsea = "Kensington and Chelsea"
    westminster = "Westminster"
    camden = "Camden"
    tower_hamlets = "Tower Hamlets"
    islington = "Islington"
    hackney = "Hackney"
    haringey = "Haringey"
    newham = "Newham"
    barking_and_bagenham = "Barking and Dagenham"
    city_of_london = "City of London"
