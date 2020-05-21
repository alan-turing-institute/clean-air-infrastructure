"""Types related to the copernicus API, but could be used elsewhere"""

from enum import Enum


class Species(Enum):
    """Valid species for API"""
    # pylint: disable=invalid-name
    NO2 = "NO2"
    PM25 = "PM25"
    PM10 = "PM10"
    O3 = "O3" # species to get data for


class Periods(Enum):
    """Valid time periods for copernicus satellite API requests"""

    day1 = "0H24H"
    day2 = "25H48H"
    day3 = "49H72H"
