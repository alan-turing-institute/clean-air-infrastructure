"""
Table for HexGrid static data
"""
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base


class HexGrid(DeferredReflection, Base):
    """Table of static hexagonal grids"""
    __tablename__ = "glahexgrid"
    __table_args__ = {'schema': 'datasources'}

    def __repr__(self):
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in [c.name for c in self.__table__.columns]]
        return "<HexGrid(" + ", ".join(vals)
