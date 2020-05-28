"""
Table for traffic data.
"""
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from cleanair.databases import Base
from cleanair.mixins import DataConfigMixin


class TrafficDataTable(Base, DataConfigMixin):
    """Storing settings for traffic data."""

    __tablename__ = "traffic_data"
    __table_args__ = {"schema": "gla_traffic"}

    # TODO this should be included in DataConfigMixin - but AQ work is not ready yet
    preprocessing = Column(JSONB, nullable=False, index=False)
