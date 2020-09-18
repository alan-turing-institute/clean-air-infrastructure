"""
Database classes and functions for traffic.
"""
from . import mixins
from .traffic_queries import ScootInstanceQuery, TrafficQuery

__all__ = [
    "mixins",
    "ScootInstanceQuery",
    "TrafficQuery",
]
