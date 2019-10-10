"""
Tables for AQE data source
"""
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


class RectGrid(Base):
    """Table of grid points"""
    __tablename__ = "rectgrid"
    __table_args__ = {"schema": "interest_points"}

    column_id = Column(Integer, primary_key=True, nullable=False)
    row_id = Column(Integer, primary_key=True, nullable=False)
    point_id = Column(UUID, ForeignKey("interest_points.meta_point.id"), nullable=False)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326, dimension=2, spatial_index=True))

    # Create RectGrid.point with no reverse relationship
    point = relationship("MetaPoint")

    def __repr__(self):
        return "<RectGrid(" + ", ".join([
            "column_id='{}'".format(self.column_id),
            "row_id='{}'".format(self.row_id),
            "point_id='{}'".format(self.point_id),
            "geom='{}'".format(self.geom),
            ])
