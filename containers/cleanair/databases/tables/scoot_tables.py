"""
Tables for SCOOT data source
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base


class ScootReading(Base):
    """Table of Scoot readings"""
    __tablename__ = "scoot_readings"
    __table_args__ = {'schema': 'datasources'}

    DetectorID = Column(String(9), primary_key=True, nullable=False)  # DETSCN
    MeasurementStartUTC = Column(TIMESTAMP, primary_key=True, nullable=False)  # TIMESTAMP
    MeasurementEndUTC = Column(TIMESTAMP, primary_key=True, nullable=False)  # TIMESTAMP
    NVehiclesInInterval = Column(Integer)  # FLOW_ACTUAL / 60
    OccupancyPercentage = Column(DOUBLE_PRECISION)  # OCCU_ACTUAL
    CongestionPercentage = Column(DOUBLE_PRECISION)  # CONG_ACTUAL
    SaturationPercentage = Column(DOUBLE_PRECISION)  # SATU_ACTUAL
    FlowRawCount = Column(Integer)  # FLOW_COUNT
    OccupancyRawCount = Column(Integer)  # OCCU_COUNT
    CongestionRawCount = Column(Integer)  # CONG_COUNT
    SaturationRawCount = Column(Integer)  # SATU_COUNT
    Region = Column(String(5))  # REGION

    def __repr__(self):
        return "<ScootReading(" + ", ".join([
            "DetectorID='{}'".format(self.DetectorID),
            "MeasurementStartUTC='{}'".format(self.MeasurementStartUTC),
            "MeasurementEndUTC='{}'".format(self.MeasurementEndUTC),
            "NVehiclesInInterval='{}'".format(self.NVehiclesInInterval),
            "OccupancyPercentage='{}'".format(self.OccupancyPercentage),
            "CongestionPercentage='{}'".format(self.CongestionPercentage),
            "SaturationPercentage='{}'".format(self.SaturationPercentage),
            "FlowRawCount='{}'".format(self.FlowRawCount),
            "OccupancyRawCount='{}'".format(self.OccupancyRawCount),
            "CongestionRawCount='{}'".format(self.CongestionRawCount),
            "SaturationRawCount='{}'".format(self.SaturationRawCount),
            "Region='{}'".format(self.Region),
            ])


class ScootDetectors(DeferredReflection, Base):
    """Table of Scoot detectors"""
    __tablename__ = "scootdetectors"
    __table_args__ = {'schema': 'datasources'}

    def __repr__(self):
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in [c.name for c in self.__table__.columns]]
        return "<ScootDetector(" + ", ".join(vals)
