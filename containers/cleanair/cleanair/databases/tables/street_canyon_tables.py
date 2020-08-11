"""
Table for OS highways static data
"""
from __future__ import annotations
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base


class StreetCanyon(DeferredReflection, Base):
    """Table of static OS highways data"""

    __tablename__ = "street_canyon"
    __table_args__ = {"schema": "static_data"}

    def __repr__(self) -> str:
        cols = [c.name for c in self.__table__.columns]
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<StreetCanyon(" + ", ".join(vals) + ")>"
