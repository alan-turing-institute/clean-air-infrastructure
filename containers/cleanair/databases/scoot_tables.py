"""
Tables for SCOOT data source
"""
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from . import BASE


class ScootReading(BASE):
    """Table of Scoot readings"""
    __tablename__ = "scoot_readings"
    __table_args__ = {'schema': 'datasources'}

    MeasurementStartUTC = Column(TIMESTAMP, primary_key=True, nullable=False)  # TIMESTAMP
    MeasurementEndUTC = Column(TIMESTAMP, primary_key=True, nullable=False)  # TIMESTAMP
    DetectorID = Column(String(9), primary_key=True, nullable=False)  # DETSCN
    Region = Column(String(5))  # REGION
    DetectorFault = Column(Boolean)  # DET
    FlowThisInterval = Column(Integer)  # FLOW_ACTUAL / 60
    OccupancyPercentage = Column(DOUBLE_PRECISION)  # OCCU_ACTUAL
    CongestionPercentage = Column(DOUBLE_PRECISION)  # CONG_ACTUAL
    SaturationPercentage = Column(DOUBLE_PRECISION)  # SATU_ACTUAL
    FlowRawCount = Column(Integer)  # FLOW_COUNT
    OccupancyRawCount = Column(Integer)  # OCCU_COUNT
    CongestionRawCount = Column(Integer)  # CONG_COUNT
    SaturationRawCount = Column(Integer)  # SATU_COUNT

    def __repr__(self):
        return "<ScootReading(" + ", ".join([
                   "MeasurementStartUTC='{}'".format(self.MeasurementStartUTC),
                   "MeasurementEndUTC='{}'".format(self.MeasurementEndUTC),
                   "DetectorID='{}'".format(self.DetectorID),
                   "Region='{}'".format(self.Region),
                   "DetectorFault='{}'".format(self.DetectorFault),
                   "FlowThisInterval='{}'".format(self.FlowThisInterval),
                   "OccupancyPercentage='{}'".format(self.OccupancyPercentage),
                   "CongestionPercentage='{}'".format(self.CongestionPercentage),
                   "SaturationPercentage='{}'".format(self.SaturationPercentage),
                   "FlowRawCount='{}'".format(self.FlowRawCount),
                   "OccupancyRawCount='{}'".format(self.OccupancyRawCount),
                   "CongestionRawCount='{}'".format(self.CongestionRawCount),
                   "SaturationRawCount='{}'".format(self.SaturationRawCount)
               ])


def initialise(engine):
    """Ensure that all tables exist"""
    BASE.metadata.create_all(engine)
