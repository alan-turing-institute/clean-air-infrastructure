"""
Tables for LAQN data source
"""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from ..base import Base


class LAQNSite(Base):
    """Table of LAQN sites"""
    __tablename__ = "laqn_site"
    __table_args__ = {"schema": "interest_points"}

    site_code = Column(String(4), primary_key=True, nullable=False)
    point_id = Column(UUID, ForeignKey("interest_points.meta_point.id"), nullable=False)
    site_type = Column(String(20), nullable=False)
    date_opened = Column(TIMESTAMP, nullable=False)
    date_closed = Column(TIMESTAMP)

    # Create LAQNSite.readings and LAQNReading.site
    readings = relationship("LAQNReading", backref="site")
    # Create LAQNSite.point with no reverse relationship
    point = relationship("InterestPoint")

    def __repr__(self):
        return "<LAQNSite(" + ", ".join([
            "site_code='{}'".format(self.site_code),
            "la_id='{}'".format(self.la_id),
            "site_type='{}'".format(self.site_type),
            "Latitude='{}'".format(self.Latitude),
            "Longitude='{}'".format(self.Longitude),
            "date_opened='{}'".format(self.date_opened),
            "date_closed='{}'".format(self.date_closed),
            ])

    @staticmethod
    def build_entry(site_dict):
        """
        Create an LAQNSite entry, replacing empty strings with None
        """
        # Replace empty strings
        site_dict = {k: (v if v else None) for k, v in site_dict.items()}

        # Construct the record and return it
        return LAQNSite(site_code=site_dict["@SiteCode"],
                        point_id=site_dict["point_id"],
                        site_type=site_dict["@SiteType"],
                        date_opened=site_dict["@DateOpened"],
                        date_closed=site_dict["@DateClosed"])


class LAQNReading(Base):
    """Table of LAQN readings"""
    __tablename__ = "laqn_reading"
    __table_args__ = {"schema": "dynamic_data"}

    site_code = Column(String(4), ForeignKey("interest_points.laqn_site.site_code"), primary_key=True, nullable=False)
    species_code = Column(String(4), primary_key=True, nullable=False)
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    value = Column(DOUBLE_PRECISION, nullable=True)

    def __repr__(self):
        return "<LAQNReading(" + ", ".join([
            "site_code='{}'".format(self.site_code),
            "species_code='{}'".format(self.species_code),
            "measurement_start_utc='{}'".format(self.measurement_start_utc),
            "measurement_end_utc='{}'".format(self.measurement_end_utc),
            "value='{}'".format(self.value),
            ])

    @staticmethod
    def build_entry(reading_dict):
        """
        Create an LAQNReading entry, replacing empty strings with None
        """
        # Replace empty strings
        reading_dict = {k: (v if v else None) for k, v in reading_dict.items()}

        # Construct the record and return it
        return LAQNReading(site_code=reading_dict["SiteCode"],
                           species_code=reading_dict["@SpeciesCode"],
                           measurement_start_utc=reading_dict["MeasurementStartUTC"],
                           measurement_end_utc=reading_dict["MeasurementEndUTC"],
                           value=reading_dict["@Value"])
