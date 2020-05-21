"""
Table for London boundary static data
"""
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base


class LondonBoundary(DeferredReflection, Base):
    """Table containing London boundary data"""

    __tablename__ = "london_boundary"
    __table_args__ = {"schema": "static_data"}

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<LondonBoundary(" + ", ".join(vals) + ")>"
