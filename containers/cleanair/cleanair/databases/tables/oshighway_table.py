"""
Table for OS highways static data
"""
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base


class OSHighway(DeferredReflection, Base):
    """Table of static OS highways data"""

    __tablename__ = "oshighway_roadlink"
    __table_args__ = {"schema": "static_data"}

    def __repr__(self):
        cols = [c.name for c in self.__table__.columns]
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<OSHighway(" + ", ".join(vals) + ")>"
