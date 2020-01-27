"""
Table for UKMap static data
"""
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base


class UKMap(DeferredReflection, Base):
    """Table of static UKMap data"""

    __tablename__ = "ukmap"
    __table_args__ = {"schema": "static_data"}

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<UKMap(" + ", ".join(vals)
