"""
Tables for AQE data source
"""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class AQESite(Base):
    """Table of AQE sites"""
    __tablename__ = "aqe_sites"
    __table_args__ = {'schema': 'datasources'}

    SiteCode = Column(String(5), primary_key=True, nullable=False)
    SiteName = Column(String(), nullable=False)
    SiteType = Column(String(20), nullable=False)
    DateOpened = Column(TIMESTAMP)
    DateClosed = Column(TIMESTAMP)
    point_id = Column(UUID, ForeignKey('buffers.interest_points.point_id'), nullable=False)

    aqe_readings = relationship("AQEReading", back_populates="aqe_site")
    aqe_interest_points = relationship("InterestPoint", back_populates="ip_aqesite")

    def __repr__(self):
        return "<AQESite(" + ", ".join([
            "SiteCode='{}'".format(self.SiteCode),
            "SiteName='{}'".format(self.SiteName),
            "SiteType='{}'".format(self.SiteType),
            "DateOpened='{}'".format(self.DateOpened),
            "DateClosed='{}'".format(self.DateClosed),
            "point_id='{}'".format(self.point_id),
            ])


class AQEReading(Base):
    """Table of AQE readings"""
    __tablename__ = "aqe_readings"
    __table_args__ = {'schema': 'datasources'}

    SiteCode = Column(String(5), ForeignKey('datasources.aqe_sites.SiteCode'), primary_key=True, nullable=False)
    SpeciesCode = Column(String(4), primary_key=True, nullable=False)
    MeasurementStartUTC = Column(TIMESTAMP, primary_key=True, nullable=False)
    MeasurementEndUTC = Column(TIMESTAMP, primary_key=True, nullable=False)
    Value = Column(DOUBLE_PRECISION, nullable=True)

    aqe_site = relationship("AQESite", back_populates="aqe_readings")

    def __repr__(self):
        return "<AQEReading(" + ", ".join([
            "SiteCode='{}'".format(self.SiteCode),
            "SpeciesCode='{}'".format(self.SpeciesCode),
            "MeasurementStartUTC='{}'".format(self.MeasurementStartUTC),
            "MeasurementEndUTC='{}'".format(self.MeasurementEndUTC),
            "Value='{}'".format(self.Value),
            ])


def build_site_entry(site_dict):
    """Create an AQESite entry, replacing empty strings with None"""
    # Replace empty strings
    site_dict = {k: (v if v else None) for k, v in site_dict.items()}

    # Construct the record and return it
    return AQESite(SiteCode=site_dict["SiteCode"],
                   SiteName=site_dict["SiteName"],
                   SiteType=site_dict["SiteType"],
                   DateOpened=site_dict["DateOpened"],
                   DateClosed=site_dict["DateClosed"],
                   point_id=site_dict["point_id"])


def build_reading_entry(reading_dict):
    """
    Create an AQEReading entry, replacing empty strings with None
    """
    # Replace empty strings
    reading_dict = {k: (v if v else None) for k, v in reading_dict.items()}

    # Construct the record and return it
    return AQEReading(SiteCode=reading_dict["SiteCode"],
                      SpeciesCode=reading_dict["SpeciesCode"],
                      MeasurementStartUTC=reading_dict["MeasurementStartUTC"],
                      MeasurementEndUTC=reading_dict["MeasurementEndUTC"],
                      Value=reading_dict["Value"])
