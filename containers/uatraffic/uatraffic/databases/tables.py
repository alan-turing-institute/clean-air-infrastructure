
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

    __table_args__ = (
        ForeignKeyConstraint(
            ["data_id"], ["gla_traffic.traffic_data.data_id"]
        ),
        ForeignKeyConstraint(
            ["model_name", "param_id"],
            ["gla_traffic.traffic_model.model_name", "gla_traffic.traffic_model.param_id"]
        ),
        # ForeignKeyConstraint(
        #     [InstanceTableMixin.model_name, InstanceTableMixin.param_id],
        #     [TrafficModelTable.model_name, TrafficModelTable.param_id]
        # ),
        {"schema": "gla_traffic"}
    )

class TrafficMetric(Base):
    """
    A table for storing metrics from traffic models.
    """

    __table_args__ = {"schema": "gla_traffic"}
    __tablename__ = "traffic_metric"

    instance_id = Column(
        String(64),
        ForeignKey("gla_traffic.traffic_instance.instance_id"),
        primary_key=True,
        nullable=False,
    )
    coverage50 = Column(Float, nullable=False, index=False)
    coverage75 = Column(Float, nullable=False, index=False)
    coverage95 = Column(Float, nullable=False, index=False)
    nlpl = Column(Float, nullable=False, index=False)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table.columns]
        ]
        return "<Instance(" + ", ".join(vals)
