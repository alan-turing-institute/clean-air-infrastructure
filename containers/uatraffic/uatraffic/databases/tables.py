
from sqlalchemy import ForeignKey
from cleanair.mixins import InstanceTableMixin
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

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table.columns]
        ]
        return "<Instance(" + ", ".join(vals)
