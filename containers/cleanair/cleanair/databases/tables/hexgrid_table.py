"""
Table for HexGrid static data
"""
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base


class HexGrid(DeferredReflection, Base):
    """Table of static hexagonal grids"""

    __tablename__ = "hexgrid"
    __table_args__ = {"schema": "interest_points"}

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [
                c.name for c in self.__table__.columns
            ]  # pylint: disable=no-member
        ]
        return "<HexGrid(" + ", ".join(vals) + ")>"
