"""
Table for traffic data.
"""
from cleanair.databases import Base
from cleanair.mixins import DataTableMixin


class TrafficDataTable(Base, DataTableMixin):
    """Storing settings for traffic data."""

    __tablename__ = "traffic_data"
    __table_args__ = {"schema": "gla_traffic"}
