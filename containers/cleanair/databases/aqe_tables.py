"""
Tables for AQE data source
"""
from sqlalchemy import Column, String, DDL, event
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry
from . import BASE


class AQESite(BASE):
    """Table of AQE sites"""
    __tablename__ = "aqe_sites"
    __table_args__ = {'schema' : 'datasources'}
    SiteCode = Column(String(5), primary_key=True, nullable=False)
    SiteName = Column(String(), nullable=False)
    SiteType = Column(String(20), nullable=False)
    Latitude = Column(DOUBLE_PRECISION)
    Longitude = Column(DOUBLE_PRECISION)
    DateOpened = Column(TIMESTAMP)
    DateClosed = Column(TIMESTAMP)
    SiteLink = Column(String)
    DataManager = Column(String)
    geom = Column(Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True))


class AQEReading(BASE):
    """Table of AQE readings"""
    __tablename__ = "aqe_readings"
    __table_args__ = {'schema' : 'datasources'}
    SiteCode = Column(String(5), primary_key=True, nullable=False)
    SpeciesCode = Column(String(4), primary_key=True, nullable=False)
    MeasurementDateGMT = Column(TIMESTAMP, primary_key=True, nullable=False)
    Value = Column(DOUBLE_PRECISION, nullable=True)


def initialise(engine):
    """Ensure that all tables exist"""
    BASE.metadata.create_all(engine)


def build_site_entry(site_dict):
    """
    Create an AQESite entry, replacing empty strings with None
    """
    # Replace empty strings
    site_dict = {k: (v if v else None) for k, v in site_dict.items()}

    # Only include geom if both latitude and longitude are available
    kwargs = {}
    if site_dict["Latitude"] and site_dict["Longitude"]:
        kwargs = {"geom": "SRID=4326;POINT({} {})".format(site_dict["Longitude"], site_dict["Latitude"])}

    # Construct the record and return it
    return AQESite(SiteCode=site_dict["SiteCode"],
                   SiteName=site_dict["SiteName"],
                   SiteType=site_dict["SiteType"],
                   Latitude=site_dict["Latitude"],
                   Longitude=site_dict["Longitude"],
                   DateOpened=site_dict["DateOpened"],
                   DateClosed=site_dict["DateClosed"],
                   SiteLink=site_dict["SiteLink"],
                   DataManager=site_dict["DataManager"],
                   **kwargs)


def build_reading_entry(reading_dict):
    """
    Create an AQEReading entry, replacing empty strings with None
    """
    # Replace empty strings
    reading_dict = {k: (v if v else None) for k, v in reading_dict.items()}

    # Construct the record and return it
    return AQEReading(SiteCode=reading_dict["@SiteCode"],
                      SpeciesCode=reading_dict["@SpeciesCode"],
                      MeasurementDateGMT=reading_dict["@MeasurementDateGMT"],
                      Value=reading_dict["@Value"])
