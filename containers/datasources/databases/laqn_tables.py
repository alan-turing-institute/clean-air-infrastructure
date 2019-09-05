from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

Base = declarative_base()


class LAQNSite(Base):
    """Table of LAQN sites"""
    __tablename__ = "laqn_sites"
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
        return "<LAQNSite(SiteCode='%s', SiteType='%s', Latitude='%s', Longitude='%s', Opened='%s', Closed='%s'" % (
            self.SiteCode, self.SiteType, self.Latitude, self.Longitude, self.DateOpened, self.DateClosed)


class LAQNReading(Base):
    """Table of LAQN readings"""
    __tablename__ = "laqn_readings"
    SiteCode = Column(String(4), ForeignKey('laqn_sites.SiteCode'), primary_key=True, nullable=False)
    SpeciesCode = Column(String(4), primary_key=True, nullable=False)
    MeasurementDateGMT = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    Value = Column(DOUBLE_PRECISION, nullable=True)

    site = relationship("LAQNSite", back_populates="readings")

    def __repr__(self):
        return "<LAQNReading(SiteCode='%s', SpeciesCode='%s', MeasurementDateGMT='%s', Value='%s'" % (
            self.SiteCode, self.SpeciesCode, self.MeasurementDateGMT, self.Value)


def initialise(engine):
    """Ensure that all tables exist"""
    Base.metadata.create_all(engine)


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

    site = LAQNSite(SiteCode=site_dict["@SiteCode"],
                    la_id=site_dict["@LocalAuthorityCode"],
                    SiteType=site_dict["@SiteType"],
                    Latitude=site_dict["@Latitude"],
                    Longitude=site_dict["@Longitude"],
                    DateOpened=site_dict["@DateOpened"],
                    DateClosed=site_dict["@DateClosed"],
                    **kwargs)

    # Construct the record and return it
    return site


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
