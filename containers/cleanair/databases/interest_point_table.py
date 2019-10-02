"""
Table for interest points
"""
import uuid
from geoalchemy2 import Geometry
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import Base


class InterestPoint(Base):
    """Table of interest points"""
    __tablename__ = "interest_points"
    __table_args__ = {"schema": "buffers"}

    source = Column(String(10), primary_key=True)
    location = Column(Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True), primary_key=True)
    point_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    ip_aqesite = relationship("AQESite", back_populates="aqe_interest_points")
    ip_laqnsite = relationship("LAQNSite", back_populates="laqn_interest_points")
    ip_rectgrid = relationship("RectGrid", back_populates="rectgrid_interest_points")
    # ip_ukmap_feature = relationship("features_UKMAP", back_populates="ukmap_features")

    def __repr__(self):
        return "<InterestPoint(" + ", ".join([
            "point_id='{}'".format(self.point_id),
            "source='{}'".format(self.source),
            "location='{}'".format(self.location),
            ])


def build_ewkt(latitude, longitude):
    """Create an EWKT geometry string from latitude and longitude"""
    return "SRID=4326;POINT({} {})".format(longitude, latitude)


def build_entry(source, latitude=None, longitude=None, geometry=None):
    """Create an InterestPoint entry from a source and position details"""
    # Attempt to convert latitude and longitude to geometry
    if not geometry:
        if latitude and longitude:
            geometry = build_ewkt(latitude, longitude)

    # Construct the record and return it
    if geometry:
        return InterestPoint(source=source, location=geometry)
    return None
