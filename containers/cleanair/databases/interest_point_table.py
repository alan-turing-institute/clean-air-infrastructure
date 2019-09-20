"""
Table for interest points
"""
import uuid
from geoalchemy2 import Geometry
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from . import Base


class InterestPoint(Base):
    """Table of interest points"""
    __tablename__ = "interest_points"
    __table_args__ = {"schema": "buffers"}

    source = Column(String(7), primary_key=True)
    location = Column(Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True), primary_key=True)
    point_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    aqe_site = relationship("AQESite", back_populates="interest_points")
    laqn_site = relationship("LAQNSite", back_populates="interest_points")

    def __repr__(self):
        return "<InterestPoint(" + ", ".join([
            "point_id='{}'".format(self.point_id),
            "source='{}'".format(self.source),
            "location='{}'".format(self.location),
            ])


def EWKT_from_lat_long(latitude, longitude):
    return "SRID=4326;POINT({} {})".format(longitude, latitude)


def build_entry(source, **kwargs):
    """
    Create an InterestPoint entry from a source and position details
    """
    # Attempt to extract a geometry argument
    geometry = kwargs.get("geometry", None)

    # Attempt to convert latitude and longitude to geometry
    if not geometry:
        latitude = kwargs.get("latitude", None)
        longitude = kwargs.get("longitude", None)
        if latitude and longitude:
            geometry = EWKT_from_lat_long(latitude, longitude)

    # Construct the record and return it
    if geometry:
        point_id = kwargs.get("point_id", None)
        if point_id:
            return InterestPoint(source=source, location=geometry, point_id=uuid)
        return InterestPoint(source=source, location=geometry)
    return None
