"""
Table that stores the parameters and details of models.
"""

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from ..base import Base

class ModelTable(Base):
    """Table of model parameters."""

    __tablename__ = "model"
    __table_args__ = {"schema": "model_results"}
    
    model_name = Column(String(64), primary_key=True, nullable=False)
    param_id = Column(String(64), primary_key=True, nullable=False)
    model_param = Column(JSONB, nullable=False, index=True)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<ModelTable(" + ", ".join(vals)
