"""
Table for interest points
"""
import uuid
from geoalchemy2 import Geometry
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from ..base import Base


class MetaPoint(Base):
    """Table of interest points"""

    __tablename__ = "meta_point"
    __table_args__ = {"schema": "interest_points"}

    source = Column(String(10), primary_key=True)
    location = Column(
        Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True),
        primary_key=True,
    )
    id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    def __repr__(self):
        return "<MetaPoint(" + ", ".join(
            [
                "id='{}'".format(self.id),
                "source='{}'".format(self.source),
                "location='{}'".format(self.location),
            ]
        )

    @staticmethod
    def build_ewkt(latitude, longitude):
        """Create an EWKT geometry string from latitude and longitude"""
        return "SRID=4326;POINT({} {})".format(longitude, latitude)

    @staticmethod
    def build_entry(source, latitude=None, longitude=None, geometry=None):
        """Create an MetaPoint entry from a source and position details"""
        # Attempt to convert latitude and longitude to geometry
        if not geometry:
            if latitude and longitude:
                geometry = MetaPoint.build_ewkt(latitude, longitude)

        # Construct the record and return it
        if geometry:
            return MetaPoint(source=source, location=geometry)
        return None
