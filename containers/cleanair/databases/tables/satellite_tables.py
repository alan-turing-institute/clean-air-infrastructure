"""
Tables for Satellite data
"""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID, INTEGER
from sqlalchemy.orm import relationship
from ..base import Base


class SatelliteSite(Base):
    """Locations of the descritised satellite locations"""
    __tablename__ = "satellite_site"
    __table_args__ = {"schema": "interest_points"}

    point_id = Column(UUID, ForeignKey("interest_points.meta_point.id"), primary_key=True, nullable=False)
    box_id = Column(INTEGER, nullable=False)

    # Create SatelliteSite.point with no reverse relationship
    point = relationship("MetaPoint")

class SatelliteForecastReading(Base):
    """Table of Satellite readings"""
    __tablename__ = "satellite_forecast"
    __table_args__ = {"schema": "dynamic_data"}

    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    box_id = Column(INTEGER, ForeignKey("interest_points.satelite_site.box_id"), primary_key=True, nullable=False)
    species_code = Column(String(4), primary_key=True, nullable=False)
    value = Column(DOUBLE_PRECISION, nullable=True)

