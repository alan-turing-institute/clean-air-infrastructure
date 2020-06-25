"""Mixins for databases."""

from .traffic_data_mixin import TrafficDataQueryMixin
from .traffic_metric_mixin import TrafficMetricQueryMixin

__all__ = [
    "TrafficDataQueryMixin",
    "TrafficMetricQueryMixin",
]
