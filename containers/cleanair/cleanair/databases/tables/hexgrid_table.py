"""
Table for HexGrid static data
"""
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base
from sqlalchemy import Column, String, BigInteger
from sqlalchemy.dialects.postgresql import (
    TIMESTAMP,
    SMALLINT,
    REAL,
    VARCHAR,
    DOUBLE_PRECISION,
    UUID  
)
from geoalchemy2 import Geometry


class HexGrid(Base):
    """Table of static hexagonal grids"""

    __tablename__ = "hexgrid"
    __table_args__ = {"schema": "interest_points"}

    hex_id = Column(BigInteger, primary_key=True, autoincrement=True)
    row_id = Column(BigInteger)
    col_id = Column(BigInteger)
    area = Column(DOUBLE_PRECISION)
    geom = Column(Geometry(geometry_type="MULTI_POLYGON", srid=4326, dimension=2, spatial_index=True))
    point_id = Column(UUID)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<HexGrid(" + ", ".join(vals) + ")>"
