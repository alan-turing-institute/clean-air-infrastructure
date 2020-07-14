"""
Table for interest points
"""
import uuid
from geoalchemy2 import Geometry # type: ignore
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base
from typing import Union


class MetaPoint(Base):
    """Table of interest points"""

    __tablename__ = "meta_point"
    __table_args__ = {"schema": "interest_points"}

    source = Column(String(10), primary_key=True)
    location = Column(
        Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True),
        primary_key=True,
    )
    id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )  # pylint: disable=invalid-name

    def __repr__(self) -> str:
        return (
            "<MetaPoint("
            + ", ".join(
                [
                    "id='{}'".format(self.id),
                    "source='{}'".format(self.source),
                    "location='{}'".format(self.location),
                ]
            )
            + ")>"
        )

    @staticmethod
    def build_ewkt(latitude: float, longitude: float) -> str:
        """Create an EWKT geometry string from latitude and longitude"""
        return "SRID=4326;POINT({} {})".format(longitude, latitude)

    @staticmethod
    def build_entry(source: str, latitude: float=None, longitude: float=None, geometry: Geometry=None) -> Union[MetaPoint, None]:
        """Create an MetaPoint entry from a source and position details"""
        # Attempt to convert latitude and longitude to geometry
        if not geometry:
            if latitude and longitude:
                geometry = MetaPoint.build_ewkt(latitude, longitude)

        # Construct the record and return it
        if geometry:
            return MetaPoint(source=source, location=geometry)
        return None
