"""Source type for a metapoint."""

from enum import Enum, unique


@unique
class Source(str, Enum):
    """Different types of source for metapoints."""

    aqe = "aqe"
    hexgrid = "hexgrid"
    laqn = "laqn"
    grid_100 = "grid_100"
    scoot = "scoot"
    satellite = "satellite"
