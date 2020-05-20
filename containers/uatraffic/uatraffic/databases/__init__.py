"""
Database classes and functions for traffic.
"""
from . import tables
from .query import TrafficInstanceQuery, TrafficQuery

__all__ = [
    "tables",
    "TrafficInstanceQuery",
    "TrafficQuery",
]
