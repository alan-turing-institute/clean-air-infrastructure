"""
Tables for AQE data source
"""
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class RectGrid(Base):
    """Table of grid points"""
    __tablename__ = "rectgrid"
    __table_args__ = {'schema': 'datasources'}

    column_id = Column(Integer, primary_key=True, nullable=False)
    row_id = Column(Integer, primary_key=True, nullable=False)
    geom = Column(Geometry(geometry_type="POLYGON", srid=4326, dimension=2, spatial_index=True))
    point_id = Column(UUID, ForeignKey('buffers.interest_points.point_id'), nullable=False)

    rectgrid_interest_points = relationship("InterestPoint", back_populates="ip_rectgrid")

    def __repr__(self):
        return "<RectGrid(" + ", ".join([
            "column_id='{}'".format(self.column_id),
            "row_id='{}'".format(self.row_id),
            "geom='{}'".format(self.geom),
            "point_id='{}'".format(self.point_id),
            ])
