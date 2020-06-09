"""
Instances that store models, data and parameter summeries.
"""

from .air_quality_instance import AirQualityInstance
from .hashing import hash_fn, hash_dict
from .instance import Instance

__all__ = ["AirQualityInstance", "Instance", "hash_fn", "hash_dict"]
