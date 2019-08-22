from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()


class ScootReading(Base):
    """Table of Scoot readings"""
    __tablename__ = "scoot_readings"
    MeasurementDateUTC = Column(TIMESTAMP, primary_key=True, nullable=False) # TIMESTAMP
    DetectorID = Column(String(9), primary_key=True, nullable=False) # DETSCN
    Region = Column(String(5), primary_key=True, nullable=False) # REGION
    DetectorFault = Column(Boolean) # DET
    FlowThisMinute = Column(DOUBLE_PRECISION) # FLOW_ACTUAL / 60
    OccupancyPercentage = Column(DOUBLE_PRECISION) # OCCU_ACTUAL
    CongestionPercentage = Column(DOUBLE_PRECISION) # CONG_ACTUAL
    SaturationPercentage = Column(DOUBLE_PRECISION) # SATU_ACTUAL
    FlowRawCount = Column(Integer) # FLOW_COUNT
    OccupancyRawCount = Column(Integer) # OCCU_COUNT
    CongestionRawCount = Column(Integer) # CONG_COUNT
    SaturationRawCount = Column(Integer) # SATU_COUNT


def initialise(engine):
    Base.metadata.create_all(engine)


def build_reading_entry(reading_dict):
    """
    Create a ScootReading entry
    """
    # Construct the record and return it
    return ScootReading(**reading_dict)
