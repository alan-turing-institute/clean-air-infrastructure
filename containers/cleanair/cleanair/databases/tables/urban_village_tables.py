"""
Table for urban village static data
"""
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base


class UrbanVillage(DeferredReflection, Base):
    """Table of urban village data"""

    __tablename__ = "urban_village"
    __table_args__ = {"schema": "static_data"}

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<UrbanVillage(" + ", ".join(vals) + ")>"
