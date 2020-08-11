"""
Table for HexGrid static data
"""
from __future__ import annotations
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base


class HexGrid(DeferredReflection, Base):
    """Table of static hexagonal grids"""

    __tablename__ = "hexgrid"
    __table_args__ = {"schema": "interest_points"}

    def __repr__(self) -> str:
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<HexGrid(" + ", ".join(vals) + ")>"
