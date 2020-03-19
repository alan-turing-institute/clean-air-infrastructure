"""
Table that summerises an instance (model + data + result).
"""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import TIMESTAMP
from ..base import Base

class InstanceTable(Base):
    """Table of Instances."""

    __tablename__ = "instance"
    __table_args__ = {"schema": "model_results"}

    instance_id = Column(String(64), primary_key=True, nullable=False)
    model_name = Column(
        String(64),
        ForeignKey("model_results.model.model_name"),
        nullable=False,
        index=False,
    )
    tag = Column(String(64), nullable=False, index=False)
    param_id = Column(
        String(64),
        ForeignKey("model_results.model.param_id"),
        nullable=False,
        index=False,
    )
    data_id = Column(
        String(64),
        ForeignKey("model_results.data_config.data_id"),
        nullable=False,
        index=False,
    )
    git_hash = Column(String(40), nullable=False, index=False)
    fit_start_time = Column(TIMESTAMP, primary_key=False, nullable=False)
    cluster_id = Column(String(64), nullable=False, index=False)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table.columns]
        ]
        return "<Instance(" + ", ".join(vals)