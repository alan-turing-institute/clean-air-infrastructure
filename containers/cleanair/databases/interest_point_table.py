"""
Table for interest points
"""
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from . import Base


class InterestPoint(Base):
    """Table of interest points"""
    __tablename__ = "interest_points"
    __table_args__ = {'schema': 'buffers'}

    point_id = Column(Integer, primary_key=True, index=True)
    source = Column(String(7))
    location = Column(Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True))

    aqe_site = relationship("AQESite", back_populates="interest_points")
    laqn_site = relationship("LAQNSite", back_populates="interest_points")

    def __repr__(self):
        return "<InterestPoint(" + ", ".join([
            "point_id='{}'".format(self.point_id),
            "source='{}'".format(self.source),
            "location='{}'".format(self.location),
            ])


def build_entry(source, latitude, longitude):
    """
    Create an InterestPoint entry from a latitude and longitude pair
    """
    # Only consider sites with both latitude and longitude available
    if not latitude and longitude:
        return None

    # Construct the record and return it
    geometry = "SRID=4326;POINT({} {})".format(longitude, latitude)
    return InterestPoint(source=source, location=geometry)
