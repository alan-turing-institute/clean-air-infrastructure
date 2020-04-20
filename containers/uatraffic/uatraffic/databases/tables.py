
from sqlalchemy import ForeignKeyConstraint, Column, String, ForeignKey, Float
from cleanair.mixins import (
    DataConfigMixin,
    InstanceTableMixin,
    ModelTableMixin,
)
from cleanair.databases import Base

class TrafficDataTable(Base, DataConfigMixin):
    __tablename__ = "traffic_data"
    __table_args__ = {"schema": "gla_traffic"}

class TrafficModelTable(Base, ModelTableMixin):
    __tablename__ = "traffic_model"
    __table_args__ = {"schema": "gla_traffic"}

class TrafficInstanceTable(Base, InstanceTableMixin):

    __tablename__ = "traffic_instance"

    model_name = Column(
        String(64),
        nullable=False,
        index=False,
    )
    param_id = Column(
        String(64),
        nullable=False,
        index=False,
    )
    data_id = Column(
        String(64),
        nullable=False,
        index=False,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            [model_name, param_id],
            [TrafficModelTable.model_name, TrafficModelTable.param_id]
        ),
        {"schema": "gla_traffic"}
    )

class TrafficMetric(Base):
    """
    A table for storing metrics from traffic models.
    """

    __table_args__ = {"schema": "gla_traffic"}
    __table_name__ = "traffic_metric"

    instance_id = Column(
        String(64),
        ForeignKey("gla_traffic.traffic_instance"),
        primary_key=True,
        nullable=False,
    )
    coverage = Column(
        Float,
        nullable=False,
        index=False,
    )

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table.columns]
        ]
        return "<Instance(" + ", ".join(vals)
