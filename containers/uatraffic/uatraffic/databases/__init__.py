"""
Database classes and functions for traffic.
"""
from .scoot_lockdown_process import LockdownProcess
from .instance import TrafficInstance
from .tables import TrafficInstanceTable

__all__ = [
    "LockdownProcess",
    "TrafficInstance",
    "TrafficInstanceTable"
]
