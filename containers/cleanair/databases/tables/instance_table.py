"""
Table that summerises an instance (model + data + result).
"""

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from ..base import Base

class InstanceTable(Base):
    """Table of Instances."""

    __tablename__ = "instance"
    __table_args__ = {"schema": "model_results"}

    instance_id = Column(String(64), primary_key=True, nullable=False)
    model_name = Column(String(64), nullable=False, index=False)    # ToDo: foreign key
    tag = Column(String(64), nullable=False, index=False)
    param_id = Column(String(64), nullable=False, index=False)  # ToDo: foreign key
    data_id = Column(String(64), nullable=False, index=False)   # ToDo: foreign key
    git_hash = Column(String(40), nullable=False, index=False)
    fit_start_time = Column(TIMESTAMP, primary_key=False, nullable=False)
    cluster_id = Column(String(64), nullable=False, index=False)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table.columns]
        ]
        return "<Instance(" + ", ".join(vals)