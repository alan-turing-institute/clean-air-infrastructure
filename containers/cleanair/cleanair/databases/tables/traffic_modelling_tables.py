"""Tables for the traffic modelling schema."""

from sqlalchemy import Column, Float, ForeignKey, String, ForeignKeyConstraint
from .. import Base
from ..mixins import DataConfigMixin, InstanceTableMixin, ModelTableMixin


class TrafficInstanceTable(Base, InstanceTableMixin):
    """Store a traffic instance."""

    __tablename__ = "traffic_instance"

    __table_args__ = (
        ForeignKeyConstraint(["data_id"], ["traffic_modelling.traffic_data.data_id"]),
        ForeignKeyConstraint(
            ["model_name", "param_id"],
            [
                "traffic_modelling.traffic_model.model_name",
                "traffic_modelling.traffic_model.param_id",
            ],
        ),
        {"schema": "traffic_modelling"},
    )


class TrafficDataTable(Base, DataConfigMixin):
    """Storing settings for traffic data."""

    __tablename__ = "traffic_data"
    __table_args__ = {"schema": "traffic_modelling"}


class TrafficModelTable(Base, ModelTableMixin):
    """Storing model parameters and information."""

    __tablename__ = "traffic_model"
    __table_args__ = {"schema": "traffic_modelling"}


class TrafficMetricTable(Base):
    """
    A table for storing metrics from traffic models.
    """

    __table_args__ = {"schema": "traffic_modelling"}
    __tablename__ = "traffic_metric"

    instance_id = Column(
        String(64),
        ForeignKey("traffic_modelling.traffic_instance.instance_id"),
        primary_key=True,
        nullable=False,
    )
    data_id = Column(
        String(64),
        ForeignKey("traffic_modelling.traffic_data.data_id"),
        primary_key=True,
        nullable=False,
    )
    coverage50 = Column(Float, nullable=False, index=False)
    coverage75 = Column(Float, nullable=False, index=False)
    coverage95 = Column(Float, nullable=False, index=False)
    nlpl = Column(Float, nullable=False, index=False)

    def __repr__(self):
        cols = [c.name for c in self.__table__.columns]
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<Instance(" + ", ".join(vals)
