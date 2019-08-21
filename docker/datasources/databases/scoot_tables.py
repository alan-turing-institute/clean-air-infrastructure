from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2 import Geometry

Base = declarative_base()


class ScootSite(Base):
    """Table of Scoot sites"""
    __tablename__ = "scoot_sites"
    SiteCode = Column(String(4), primary_key=True, nullable=False)
    la_id = Column(Integer, nullable=False)
    SiteType = Column(String(20), nullable=False)
    os_grid_x = Column(DOUBLE_PRECISION)
    os_grid_y = Column(DOUBLE_PRECISION)
    Latitude = Column(DOUBLE_PRECISION)
    Longitude = Column(DOUBLE_PRECISION)
    DateOpened = Column(TIMESTAMP, nullable=False)
    DateClosed = Column(TIMESTAMP)
    geom = Column(Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True))


class ScootReading(Base):
    """Table of Scoot readings"""
    __tablename__ = "scoot_readings"
    SiteCode = Column(String(4), primary_key=True, nullable=False)
    SpeciesCode = Column(String(4), primary_key=True, nullable=False)
    MeasurementDateGMT = Column(TIMESTAMP, primary_key=True, nullable=False)
    Value = Column(DOUBLE_PRECISION, nullable=True)


def initialise(engine):
    Base.metadata.create_all(engine)


def build_site_entry(site_dict):
    """
    Create an ScootSite entry, replacing empty strings with None
    """
    # Replace empty strings
    site_dict = {k: (v if v else None) for k, v in site_dict.items()}

    # Only include geom if both latitude and longitude are available
    kwargs = {}
    if site_dict["@Latitude"] and site_dict["@Longitude"]:
        kwargs = {"geom": "SRID=4326;POINT({} {})".format(site_dict["@Longitude"], site_dict["@Latitude"])}

    # Construct the record and return it
    return ScootSite(SiteCode=site_dict["@SiteCode"],
                     la_id=site_dict["@LocalAuthorityCode"],
                     SiteType=site_dict["@SiteType"],
                     Latitude=site_dict["@Latitude"],
                     Longitude=site_dict["@Longitude"],
                     DateOpened=site_dict["@DateOpened"],
                     DateClosed=site_dict["@DateClosed"],
                     **kwargs)


def build_reading_entry(reading_dict):
    """
    Create an ScootReading entry, replacing empty strings with None
    """
    # Replace empty strings
    reading_dict = {k: (v if v else None) for k, v in reading_dict.items()}

    # Construct the record and return it
    return ScootReading(SiteCode=reading_dict["@SiteCode"],
                        SpeciesCode=reading_dict["@SpeciesCode"],
                        MeasurementDateGMT=reading_dict["@MeasurementDateGMT"],
                        Value=reading_dict["@Value"])
