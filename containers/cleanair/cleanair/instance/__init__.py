"""
Instances that store models, data and parameter summeries.
"""

from .air_quality_instance import AirQualityInstance
from .air_quality_result import AirQualityResult
from .hashing import hash_fn, hash_dict
from .instance import Instance

__all__ = [
    "AirQualityInstance",
    "AirQualityResult",
    "Instance",
    "hash_fn",
    "hash_dict",
]
