"""
Tables for intersection between datasource and interest points
"""

from sqlalchemy import Column, ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from . import Base


class IntersectionUKMAP(Base):
    """Intersection between interest points and UKMap"""
    __tablename__ = "buffers_ukmap"
    __table_args__ = {'schema': 'buffers'}

    point_id = Column(UUID, ForeignKey('buffers.interest_points.point_id'), primary_key=True, nullable=False)
    geographic_type_number = Column(Integer, primary_key=True, nullable=False)
  
    intersect_1000 = Column(Geometry(geometry_type='GEOMETRY', srid=4326, dimension=3, spatial_index=True))
    intersect_500 = Column(Geometry(geometry_type='GEOMETRY', srid=4326, dimension=3, spatial_index=True))
    intersect_200 = Column(Geometry(geometry_type='GEOMETRY', srid=4326, dimension=3, spatial_index=True))
    intersect_100 = Column(Geometry(geometry_type='GEOMETRY', srid=4326, dimension=3, spatial_index=True))
    intersect_10 = Column(Geometry(geometry_type='GEOMETRY', srid=4326, dimension=3, spatial_index=True))