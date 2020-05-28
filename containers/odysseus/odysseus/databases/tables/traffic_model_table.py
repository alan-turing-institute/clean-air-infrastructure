"""Storing model parameters."""

from cleanair.databases import Base
from cleanair.mixins import ModelTableMixin


class TrafficModelTable(Base, ModelTableMixin):
    """Storing model parameters and information."""

    __tablename__ = "traffic_model"
    __table_args__ = {"schema": "gla_traffic"}
