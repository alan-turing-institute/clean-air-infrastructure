"""
Tables for intersection between datasource and interest points
"""

from sqlalchemy import Column, ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from . import Base


class Intersection(Base):
    """Base class for buffer intersection"""
    __table_args__ = {'schema': 'buffers'}

    point_id = Column(UUID, ForeignKey('buffers.interest_points.point_id'), nullable=False)


class IntersectionUKMAP(Intersection):
    """Intersection between interest points and UKMap"""
    __tablename__ = "buffers_ukmap"

    input_id = Column(Integer, ForeignKey('datasources.ukmap.geographic_type_number'), nullable=False)
    interest_points = relationship("InterestPoint", back_populates="buffers_ukmap")
