"""Table for traffic instance."""

from sqlalchemy import ForeignKeyConstraint
from cleanair.databases import Base
from cleanair.mixins import InstanceTableMixin


class TrafficInstanceTable(Base, InstanceTableMixin):
    """Store a traffic instance."""

    __tablename__ = "traffic_instance"

    __table_args__ = (
        ForeignKeyConstraint(["data_id"], ["gla_traffic.traffic_data.data_id"]),
        ForeignKeyConstraint(
            ["model_name", "param_id"],
            [
                "gla_traffic.traffic_model.model_name",
                "gla_traffic.traffic_model.param_id",
            ],
        ),
        {"schema": "gla_traffic"},
    )
