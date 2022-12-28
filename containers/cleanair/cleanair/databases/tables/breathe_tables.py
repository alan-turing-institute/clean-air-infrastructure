"""
Tables for Breathe London(BL) data source
"""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from ..base import Base


class BreatheSite(Base):
    """Table of BL data sites"""
    
    __tablename__ = "breathe_site"
    __table_args__ = {"schema": "interest_points"}

    site_code = Column(String(8), primary_key=True, nullable=False)
    point_id = Column(
        UUID(as_uuid=True), ForeignKey("interest_points.meta_point.id"), nullable=False
    )
    site_name = Column(String(), nullable=False)
    site_type = Column(String(20), nullable=True)
    date_opened = Column(TIMESTAMP, nullable=False)
    date_closed = Column(TIMESTAMP)

    # Create BreatheSite.readings and BLReading.site
    readings = relationship("BreatheReading", backref="site")
    # Create BreatheSite.point with no reverse relationship
    point = relationship("MetaPoint")

    def __repr__(self):
        cols = [c.name for c in self.__table__.columns]
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<BreatheSite(" + ", ".join(vals) + ")>"

    @staticmethod
    def build_entry(site_dict):
        """Create a BreatheSite entry, replacing empty strings with None"""
        # Replace empty strings
        site_dict = {k: (v if v else None) for k, v in site_dict.items()}

        # Construct the record and return it
        return BreatheSite(
            site_code=site_dict["@SiteCode"],
            point_id=site_dict["point_id"],
            site_name=site_dict["@SiteName"],
            site_type=site_dict["@SiteClassification"],
            date_opened=site_dict["@StartDate"],
            date_closed=site_dict["@EndDate"],
        )
    
class BreatheReading(Base):
    """Table of Breathe London data readings"""

    __tablename__ = "breathe_reading"
    __table_args__ = {"schema": "dynamic_data"}

    site_code = Column(
        String(8),
        ForeignKey("interest_points.breathe_site.site_code"),
        primary_key=True,
        nullable=False,
    )
    measurement_start_utc = Column(
        TIMESTAMP, primary_key=True, nullable=False, index=True
    )
    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    NO2_value = Column(DOUBLE_PRECISION, nullable=True)
    PM10_value = Column(DOUBLE_PRECISION, nullable=True)
    PM25_value = Column(DOUBLE_PRECISION, nullable=True)

    def __repr__(self):
        cols = [c.name for c in self.__table__.columns]
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<BreatheReading(" + ", ".join(vals) + ")>"
    
    # @staticmethod
    # def build_entry(reading_dict, return_dict=False):
    #     """
    #     Create an BreatheReading entry, replacing empty strings with None
    #     If return_dict then return a dictionary rather than and entry, to allow inserting via sqlalchemy core
    #     """
    #     # Replace empty strings
    #     reading_dict = {k: (v if v else None) for k, v in reading_dict.items()}

    #     if return_dict:
    #         new_key = [
    #             "site_code",
    #             "measurement_star_utc",
    #             "measurement_end_utc",
    #             "NO2_value",
    #             "PM10_value",
    #             "PM25_value",
    #         ]
    #         old_key = [
    #             "SiteCode",
    #             "SpeciesCode",
    #             "MeasurementStartUTC",
    #             "MeasurementEndUTC",
    #             "Value",
    #         ]

    #         for i, key in enumerate(old_key):
    #             reading_dict[new_key[i]] = reading_dict.pop(key)
    #         return reading_dict

    #     # Construct the record and return it
    #     return BreatheReading(
    #         site_code=reading_dict["SiteCode"],
    #         species_code=reading_dict["SpeciesCode"],
    #         measurement_start_utc=reading_dict["MeasurementStartUTC"],
    #         measurement_end_utc=reading_dict["MeasurementEndUTC"],
    #         value=reading_dict["Value"],
    #     )
