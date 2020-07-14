"""
Tables for LAQN data source
"""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from ..base import Base
from typing import Any, Union, Dict


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
    readings = relationship("LAQNReading", backref="site") # type: ignore # sqlalchemy.orm.RelationshipProperty

    # Create LAQNSite.point with no reverse relationship
    point = relationship("MetaPoint") # type: ignore # sqlalchemy.orm.RelationshipProperty

    def __repr__(self) -> str:
        return (
            "<LAQNSite("
            + ", ".join(
                [
                    "site_code='{}'".format(self.site_code),
                    "point_id='{}'".format(self.point_id),
                    "site_type='{}'".format(self.site_type),
                    "date_opened='{}'".format(self.date_opened),
                    "date_closed='{}'".format(self.date_closed),
                ]
            )
            + ")>"
        )

    @staticmethod
    def build_entry(site_dict: Dict[str, Any]) -> LAQNSite:
        """
        Create an LAQNSite entry, replacing empty strings with None
        """
        # Replace empty strings
        site_dict = {k: (v if v else None) for k, v in site_dict.items()}

        # Construct the record and return it
        return LAQNSite(
            site_code=site_dict["@SiteCode"],
            point_id=site_dict["point_id"],
            site_type=site_dict["@SiteType"],
            date_opened=site_dict["@DateOpened"],
            date_closed=site_dict["@DateClosed"],
        )


class LAQNReading(Base):
    """Table of LAQN readings"""

    __tablename__ = "laqn_reading"
    __table_args__ = {"schema": "dynamic_data"}

    site_code = Column(
        String(4),
        ForeignKey("interest_points.laqn_site.site_code"),
        primary_key=True,
        nullable=False,
    )
    species_code = Column(String(4), primary_key=True, nullable=False)
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    value = Column(DOUBLE_PRECISION, nullable=True)

    def __repr__(self) -> str:
        return (
            "<LAQNReading("
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
    def build_entry(reading_dict: Dict[str, Any], return_dict: bool=False) -> Union[Dict[str, Any], LAQNReading]:
        """
        Create an LAQNReading entry, replacing empty strings with None
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
                "@SpeciesCode",
                "MeasurementStartUTC",
                "MeasurementEndUTC",
                "@Value",
            ]

            for i, key in enumerate(old_key):
                reading_dict[new_key[i]] = reading_dict.pop(key)
            return reading_dict
        # Construct the record and return it
        return LAQNReading(
            site_code=reading_dict["SiteCode"],
            species_code=reading_dict["@SpeciesCode"],
            measurement_start_utc=reading_dict["MeasurementStartUTC"],
            measurement_end_utc=reading_dict["MeasurementEndUTC"],
            value=reading_dict["@Value"],
        )
