"""Tables for the traffic modelling schema."""

from sqlalchemy import Column, Float, Integer, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from ..base import Base
from ..mixins import DataTableMixin, InstanceTableMixin, MetricsTableMixin, ModelTableMixin, ResultTableMixin


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


class TrafficDataTable(Base, DataTableMixin):
    """Storing settings for traffic data."""

    __tablename__ = "traffic_data"
    __table_args__ = {"schema": "traffic_modelling"}


class TrafficModelTable(Base, ModelTableMixin):
    """Storing model parameters and information."""

    __tablename__ = "traffic_model"
    __table_args__ = {"schema": "traffic_modelling"}


class TrafficMetricTable(Base, MetricsTableMixin):
    """
    A table for storing metrics from traffic models.
    """

    __table_args__ = (
        ForeignKeyConstraint(
            ["data_id"], ["traffic_modelling.traffic_data.data_id"]
        ),
        ForeignKeyConstraint(
            ["instance_id"], ["traffic_modelling.traffic_instance.instance_id"]
        ),
        {"schema": "traffic_modelling"},
    )
    __tablename__ = "traffic_metric"

    coverage50 = Column(Float, nullable=False, index=False)
    coverage75 = Column(Float, nullable=False, index=False)
    coverage95 = Column(Float, nullable=False, index=False)
    nlpl = Column(Float, nullable=False, index=False)

class TrafficResultTable(Base, ResultTableMixin):
    """A table for storing the results of a traffic model prediction."""

    __tablename__ = "traffic_result"

    __table_args__ = (
        ForeignKeyConstraint(
            ["data_id"], ["traffic_modelling.traffic_data.data_id"]
        ),
        ForeignKeyConstraint(
            ["instance_id"], ["traffic_modelling.traffic_instance.instance_id"]
        ),
        {"schema": "traffic_modelling"},
    )

    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    n_vehicles_in_interval = Column(Integer)
    occupancy_percentage = Column(DOUBLE_PRECISION, nullable=True)
    congestion_percentage = Column(DOUBLE_PRECISION, nullable=True)
    saturation_percentage = Column(DOUBLE_PRECISION, nullable=True)
