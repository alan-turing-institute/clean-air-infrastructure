"""
Database classes and functions for traffic.
"""
from .query import TrafficQuery, TrafficInstanceQuery
from .instance import TrafficInstance
from .tables import (
    TrafficDataTable,
    TrafficInstanceTable,
    TrafficModelTable,
)

__all__ = [
    "TrafficQuery",
    "TrafficInstance",
    "TrafficInstanceQuery",
    "TrafficDataTable",
    "TrafficInstanceTable",
    "TrafficModelTable",
]
