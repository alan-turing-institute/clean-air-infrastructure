"""
Class for querying traffic and scoot data.
"""


from cleanair.databases import DBReader
from cleanair.mixins import ScootQueryMixin
from ..mixins import (
    TrafficInstanceQueryMixin,
    TrafficDataQueryMixin,
)

class TrafficQuery(DBReader, ScootQueryMixin):
    """Query traffic data."""

    def __init__(self, secretfile: str = None, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)

class TrafficInstanceQuery(DBReader, TrafficInstanceQueryMixin, TrafficDataQueryMixin):
    """Query traffic instances."""

    def __init__(self, secretfile: str = None, **kwargs):
        super().__init__(secretfile=secretfile, **kwargs)
