"""
Tables for LAQN data source
"""
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from . import BASE


class LAQNSite(BASE):
    """Table of LAQN sites"""
    __tablename__ = "laqn_sites"
    __table_args__ = {'schema': 'datasources'}

    SiteCode = Column(String(4), primary_key=True, nullable=False)
    la_id = Column(Integer, nullable=False)
    SiteType = Column(String(20), nullable=False)
    Latitude = Column(DOUBLE_PRECISION)
    Longitude = Column(DOUBLE_PRECISION)
    DateOpened = Column(TIMESTAMP, nullable=False)
    DateClosed = Column(TIMESTAMP)
    geom = Column(Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True))

    readings = relationship("LAQNReading", back_populates="site")

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


class LAQNReading(BASE):
    """Table of LAQN readings"""
    __tablename__ = "laqn_readings"
    __table_args__ = {'schema': 'datasources'}

    SiteCode = Column(String(4), ForeignKey('datasources.laqn_sites.SiteCode'), primary_key=True, nullable=False)
    SpeciesCode = Column(String(4), primary_key=True, nullable=False)
    MeasurementStartUTC = Column(TIMESTAMP, primary_key=True, nullable=False)
    MeasurementEndUTC = Column(TIMESTAMP, primary_key=True, nullable=False)
    Value = Column(DOUBLE_PRECISION, nullable=True)

    site = relationship("LAQNSite", back_populates="readings")

    def __repr__(self):
        return "<LAQNReading(" + ", ".join([
                   "SiteCode='{}'".format(self.SiteCode),
                   "SpeciesCode='{}'".format(self.SpeciesCode),
                   "MeasurementStartUTC='{}'".format(self.MeasurementStartUTC),
                   "MeasurementEndUTC='{}'".format(self.MeasurementEndUTC),
                   "Value='{}'".format(self.Value),
               ])


def initialise(engine):
    """Ensure that all tables exist"""

    BASE.metadata.create_all(engine)


def build_site_entry(site_dict):
    """
    Create an LAQNSite entry, replacing empty strings with None
    """
    # Replace empty strings
    site_dict = {k: (v if v else None) for k, v in site_dict.items()}

    # Only include geom if both latitude and longitude are available
    kwargs = {}
    if site_dict["@Latitude"] and site_dict["@Longitude"]:
        kwargs = {"geom": "SRID=4326;POINT({} {})".format(site_dict["@Longitude"], site_dict["@Latitude"])}

    # Construct the record and return it
    return LAQNSite(SiteCode=site_dict["@SiteCode"],
                    la_id=site_dict["@LocalAuthorityCode"],
                    SiteType=site_dict["@SiteType"],
                    Latitude=site_dict["@Latitude"],
                    Longitude=site_dict["@Longitude"],
                    DateOpened=site_dict["@DateOpened"],
                    DateClosed=site_dict["@DateClosed"],
                    **kwargs)


def build_reading_entry(reading_dict):
    """
    Create an LAQNReading entry, replacing empty strings with None
    """
    # Replace empty strings
    reading_dict = {k: (v if v else None) for k, v in reading_dict.items()}

    # Construct the record and return it
    return LAQNReading(SiteCode=reading_dict["@SiteCode"],
                       SpeciesCode=reading_dict["@SpeciesCode"],
                       MeasurementDateGMT=reading_dict["@MeasurementDateGMT"],
                       Value=reading_dict["@Value"])
