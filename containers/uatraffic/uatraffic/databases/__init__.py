"""
Database classes and functions for traffic.
"""
from .query import TrafficInstanceQuery, TrafficQuery
from .instance import TrafficInstance
from .tables import (
    TrafficDataTable,
    TrafficInstanceTable,
    TrafficMetricTable,
    TrafficModelTable,
)

__all__ = [
    "TrafficInstance",
    "TrafficInstanceQuery",
    "TrafficDataTable",
    "TrafficInstanceTable",
    "TrafficMetricTable",
    "TrafficModelTable",
    "TrafficQuery",
]
