"""
Table for HexGrid static data
"""

from sqlalchemy import Column, BigInteger
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, UUID
from geoalchemy2 import Geometry
from ..base import Base


class HexGrid(Base):
    """Table of static hexagonal grids"""

    __tablename__ = "hexgrid"
    __table_args__ = {"schema": "interest_points"}

    hex_id = Column(BigInteger, primary_key=True, autoincrement=True)
    row_id = Column(BigInteger)
    col_id = Column(BigInteger)
    area = Column(DOUBLE_PRECISION)
    geom = Column(
        Geometry(
            geometry_type="MULTI_POLYGON", srid=4326, dimension=2, spatial_index=True
        )
    )
    point_id = Column(UUID)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<HexGrid(" + ", ".join(vals) + ")>"
