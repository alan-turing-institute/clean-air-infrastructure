"""
Database classes and functions for traffic.
"""
from .percentage_change import TrafficPercentageChange
from .scan_stats import ScanScoot

__all__ = [
    "ScanScoot",
    "TrafficPercentageChange",
]
