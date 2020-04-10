"""
Database classes and functions for traffic.
"""
from .scoot_lockdown_process import LockdownProcess
from .instance import TrafficInstance
from .tables import (
    TrafficDataTable,
    TrafficInstanceTable,
    TrafficModelTable,
)

__all__ = [
    "LockdownProcess",
    "TrafficInstance",
    "TrafficDataTable",
    "TrafficInstanceTable",
    "TrafficModelTable",
]
