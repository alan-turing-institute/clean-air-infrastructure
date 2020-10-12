"""
Class for querying traffic and scoot data.
"""


from cleanair.databases import DBReader
from cleanair.databases.tables import (
    TrafficInstanceTable,
    TrafficDataTable,
    TrafficModelTable,
)
from cleanair.mixins import ScootQueryMixin, InstanceQueryMixin
from .mixins import TrafficDataQueryMixin


class TrafficQuery(DBReader, ScootQueryMixin):
    """Query traffic data."""

    def __init__(self, secretfile: str = None, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)


class TrafficInstanceQuery(DBReader, InstanceQueryMixin, TrafficDataQueryMixin):
    """Query traffic instances."""

    @property
    def data_table(self) -> TrafficDataTable:
        """Data table."""
        return TrafficDataTable

    @property
    def instance_table(self) -> TrafficInstanceTable:
        """Instances for traffic table."""
        return TrafficInstanceTable

    @property
    def model_table(self) -> TrafficModelTable:
        """Model parameters for traffic models."""
        return TrafficModelTable
