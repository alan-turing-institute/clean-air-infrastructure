
from sqlalchemy import ForeignKey
from cleanair.mixins import (
    DataConfigMixin,
    InstanceTableMixin,
    ModelTableMixin,
)
from cleanair.databases import Base

class TrafficInstanceTable(Base, InstanceTableMixin):
    
    __table_args__ = {"schema": "gla_traffic"}

    InstanceTableMixin.model_name.append_foreign_key(
        ForeignKey("gla_traffic.model.model_name")
    )

    InstanceTableMixin.param_id.append_foreign_key(
        ForeignKey("gla_traffic.model.param_id")
    )

    InstanceTableMixin.data_id.append_foreign_key(
        ForeignKey("gla_traffic.data_config.data_id")
    )

class TrafficDataTable(Base, DataConfigMixin):
    __table_args__ = {"schema": "gla_traffic"}

class TrafficModelTable(Base, ModelTableMixin):
    __table_args__ = {"schema": "gla_traffic"}
