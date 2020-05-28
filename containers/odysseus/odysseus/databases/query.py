"""
Class for querying traffic and scoot data.
"""


from cleanair.databases import DBReader
from cleanair.mixins import ScootQueryMixin, InstanceQueryMixin
from .mixins import TrafficDataQueryMixin
from .tables import TrafficInstanceTable, TrafficDataTable, TrafficModelTable


class TrafficQuery(DBReader, ScootQueryMixin):
    """Query traffic data."""

    def __init__(self, secretfile: str = None, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)


class TrafficInstanceQuery(DBReader, InstanceQueryMixin, TrafficDataQueryMixin):
    """Query traffic instances."""

    def __init__(self, secretfile: str = None, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)
        self.instance_table = TrafficInstanceTable
        self.model_table = TrafficModelTable
        self.data_table = TrafficDataTable
