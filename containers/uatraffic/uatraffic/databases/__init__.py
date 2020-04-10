"""
Database classes and functions for traffic.
"""
from .query import TrafficQuery
from .instance import TrafficInstance
from .tables import (
    TrafficDataTable,
    TrafficInstanceTable,
    TrafficModelTable,
)

__all__ = [
    "TrafficQuery",
    "TrafficInstance",
    "TrafficDataTable",
    "TrafficInstanceTable",
    "TrafficModelTable",
]
