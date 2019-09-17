"""
Table for interest points
"""
from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.orm import relationship
from . import Base


class InterestPoint(DeferredReflection, Base):
    """Table of interest points"""
    __tablename__ = "interest_points"
    __table_args__ = {'schema': 'buffers'}

    aqe_site = relationship("AQESite", back_populates="interest_points")
    laqn_site = relationship("LAQNSite", back_populates="interest_points")

    def __repr__(self):
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in [c.name for c in self.__table__.columns]]
        return "<InterestPoint(" + ", ".join(vals)


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
