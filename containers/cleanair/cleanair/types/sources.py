"""Source type for a metapoint."""

from enum import Enum, unique

@unique
class Source(Enum):
    """Different types of source for metapoints."""

    aqe: str = "aqe"
    hexgrid: str = "hexgrid"
    laqn: str = "laqn"
    grid_100: str = "grid_100"
    scoot: str = "scoot"
