"""
Tables for AQE data source
"""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from ..base import Base


class AQESite(Base):
    """Table of AQE sites"""

    __tablename__ = "aqe_site"
    __table_args__ = {"schema": "interest_points"}

    site_code = Column(String(5), primary_key=True, nullable=False)
    point_id = Column(
        UUID(as_uuid=True), ForeignKey("interest_points.meta_point.id"), nullable=False
    )
    site_name = Column(String(), nullable=False)
    site_type = Column(String(20), nullable=False)
    date_opened = Column(TIMESTAMP)
    date_closed = Column(TIMESTAMP)

    # Create AQESite.readings and AQEReading.site
    readings = relationship("AQEReading", backref="site")
    # Create AQESite.point with no reverse relationship
    point = relationship("MetaPoint")

    def __repr__(self):
        return (
            "<AQESite("
            + ", ".join(
                [
                    "site_code='{}'".format(self.site_code),
                    "point_id='{}'".format(self.point_id),
                    "site_name='{}'".format(self.site_name),
                    "site_type='{}'".format(self.site_type),
                    "date_opened='{}'".format(self.date_opened),
                    "date_closed='{}'".format(self.date_closed),
                ]
            )
            + ")>"
        )

    @staticmethod
    def build_entry(site_dict):
        """Create an AQESite entry, replacing empty strings with None"""
        # Replace empty strings
        site_dict = {k: (v if v else None) for k, v in site_dict.items()}

        # Construct the record and return it
        return AQESite(
            site_code=site_dict["SiteCode"],
            point_id=site_dict["point_id"],
            site_name=site_dict["SiteName"],
            site_type=site_dict["SiteType"],
            date_opened=site_dict["DateOpened"],
            date_closed=site_dict["DateClosed"],
        )


class AQEReading(Base):
    """Table of AQE readings"""

    __tablename__ = "aqe_reading"
    __table_args__ = {"schema": "dynamic_data"}

    site_code = Column(
        String(5),
        ForeignKey("interest_points.aqe_site.site_code"),
        primary_key=True,
        nullable=False,
    )
    species_code = Column(String(4), primary_key=True, nullable=False)
    measurement_start_utc = Column(
        TIMESTAMP, primary_key=True, nullable=False, index=True
    )
    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    value = Column(DOUBLE_PRECISION, nullable=True)

    def __repr__(self):
        return (
            "<AQEReading("
            + ", ".join(
                [
                    "site_code='{}'".format(self.site_code),
                    "species_code='{}'".format(self.species_code),
                    "measurement_start_utc='{}'".format(self.measurement_start_utc),
                    "measurement_end_utc='{}'".format(self.measurement_end_utc),
                    "value='{}'".format(self.value),
                ]
            )
            + ")>"
        )

    @staticmethod
    def build_entry(reading_dict, return_dict=False):
        """
        Create an AQEReading entry, replacing empty strings with None
        If return_dict then return a dictionary rather than and entry, to allow inserting via sqlalchemy core
        """
        # Replace empty strings
        reading_dict = {k: (v if v else None) for k, v in reading_dict.items()}

        if return_dict:
            new_key = [
                "site_code",
                "species_code",
                "measurement_start_utc",
                "measurement_end_utc",
                "value",
            ]
            old_key = [
                "SiteCode",
                "SpeciesCode",
                "MeasurementStartUTC",
                "MeasurementEndUTC",
                "Value",
            ]

            for i, key in enumerate(old_key):
                reading_dict[new_key[i]] = reading_dict.pop(key)
            return reading_dict

        # Construct the record and return it
        return AQEReading(
            site_code=reading_dict["SiteCode"],
            species_code=reading_dict["SpeciesCode"],
            measurement_start_utc=reading_dict["MeasurementStartUTC"],
            measurement_end_utc=reading_dict["MeasurementEndUTC"],
            value=reading_dict["Value"],
        )
