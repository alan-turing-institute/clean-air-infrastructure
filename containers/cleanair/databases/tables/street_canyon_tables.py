"""
Table for OS highways static data
"""
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base


class StreetCanyon(DeferredReflection, Base):
    """Table of static OS highways data"""

    __tablename__ = "street_canyon"
    __table_args__ = {"schema": "static_data"}

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<StreetCanyon(" + ", ".join(vals) + ")>"
