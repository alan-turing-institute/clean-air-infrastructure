"""
Table for traffic data.
"""
from cleanair.databases import Base
from cleanair.mixins import DataConfigMixin


class TrafficDataTable(Base, DataConfigMixin):
    """Storing settings for traffic data."""

    __tablename__ = "traffic_data"
    __table_args__ = {"schema": "gla_traffic"}    
