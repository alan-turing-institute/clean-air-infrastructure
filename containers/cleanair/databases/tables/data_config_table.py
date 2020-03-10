from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from ..base import Base

class DataConfig(Base):
    """Table of model parameters."""

    __tablename__ = "data_config"
    __table_args__ = {"schema": "model_results"}
    
    data_id = Column(String(64), primary_key=True, nullable=False)
    data_config = Column(JSONB, nullable=False, index=True)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<DataConfig(" + ", ".join(vals)