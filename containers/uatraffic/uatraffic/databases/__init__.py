"""
Database classes and functions for traffic.
"""
from . import tables
from .query import TrafficInstanceQuery, TrafficQuery
from .instance import TrafficInstance

__all__ = [
    "tables",
    "TrafficInstance",
    "TrafficInstanceQuery",
    "TrafficQuery",
]
