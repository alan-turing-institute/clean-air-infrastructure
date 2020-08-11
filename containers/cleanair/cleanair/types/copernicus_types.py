"""Types related to the copernicus API, but could be used elsewhere"""

from __future__ import annotations
from enum import Enum


class Species(Enum):
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
