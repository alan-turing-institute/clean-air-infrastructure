"""
Tables for LAQN data source
"""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class LAQNSite(Base):
    """Table of LAQN sites"""
    __tablename__ = "laqn_sites"
    __table_args__ = {'schema': 'datasources'}

    SiteCode = Column(String(4), primary_key=True, nullable=False)
    SiteType = Column(String(20), nullable=False)
    DateOpened = Column(TIMESTAMP, nullable=False)
    DateClosed = Column(TIMESTAMP)
    point_id = Column(UUID, ForeignKey('buffers.interest_points.point_id'), nullable=False)

    laqn_readings = relationship("LAQNReading", back_populates="laqn_site")
    laqn_interest_points = relationship("InterestPoint", back_populates="ip_laqnsite")

    def __repr__(self):
        return "<LAQNSite(" + ", ".join([
            "SiteCode='{}'".format(self.SiteCode),
            "la_id='{}'".format(self.la_id),
            "SiteType='{}'".format(self.SiteType),
            "Latitude='{}'".format(self.Latitude),
            "Longitude='{}'".format(self.Longitude),
            "DateOpened='{}'".format(self.DateOpened),
            "DateClosed='{}'".format(self.DateClosed),
            ])


class LAQNReading(Base):
    """Table of LAQN readings"""
    __tablename__ = "laqn_readings"
    __table_args__ = {'schema': 'datasources'}

    SiteCode = Column(String(4), ForeignKey('datasources.laqn_sites.SiteCode'), primary_key=True, nullable=False)
    SpeciesCode = Column(String(4), primary_key=True, nullable=False)
    MeasurementStartUTC = Column(TIMESTAMP, primary_key=True, nullable=False)
    MeasurementEndUTC = Column(TIMESTAMP, primary_key=True, nullable=False)
    Value = Column(DOUBLE_PRECISION, nullable=True)

    laqn_site = relationship("LAQNSite", back_populates="laqn_readings")

    def __repr__(self):
        return "<LAQNReading(" + ", ".join([
            "SiteCode='{}'".format(self.SiteCode),
            "SpeciesCode='{}'".format(self.SpeciesCode),
            "MeasurementStartUTC='{}'".format(self.MeasurementStartUTC),
            "MeasurementEndUTC='{}'".format(self.MeasurementEndUTC),
            "Value='{}'".format(self.Value),
            ])


def build_site_entry(site_dict):
    """
    Create an LAQNSite entry, replacing empty strings with None
    """
    # Replace empty strings
    site_dict = {k: (v if v else None) for k, v in site_dict.items()}

    # Construct the record and return it
    return LAQNSite(SiteCode=site_dict["@SiteCode"],
                    SiteType=site_dict["@SiteType"],
                    DateOpened=site_dict["@DateOpened"],
                    DateClosed=site_dict["@DateClosed"],
                    point_id=site_dict["point_id"])


def build_reading_entry(reading_dict):
    """
    Create an LAQNReading entry, replacing empty strings with None
    """
    # Replace empty strings
    reading_dict = {k: (v if v else None) for k, v in reading_dict.items()}

    # Construct the record and return it
    return LAQNReading(SiteCode=reading_dict["SiteCode"],
                       SpeciesCode=reading_dict["@SpeciesCode"],
                       MeasurementStartUTC=reading_dict["MeasurementStartUTC"],
                       MeasurementEndUTC=reading_dict["MeasurementEndUTC"],
                       Value=reading_dict["@Value"])
