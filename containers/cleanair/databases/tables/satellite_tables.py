"""
Tables for Satellite data
"""
import uuid
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from geoalchemy2 import Geometry
from ..base import Base


class SatelliteBox(Base):
    """Locations of the discretised satellite locations"""

    __tablename__ = "satellite_box"
    __table_args__ = {"schema": "interest_points"}

    centroid = Column(
        Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True),
        primary_key=True,
    )
    geom = Column(
        Geometry(geometry_type="POLYGON", srid=4326, dimension=2, spatial_index=True),
    )
    id = Column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )  # pylint: disable=invalid-name

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<SatelliteBox(" + ", ".join(vals) + ")>"

    @staticmethod
    def build_ewkt(latitude, longitude):
        """Create an EWKT geometry string from latitude and longitude"""
        return "SRID=4326;POINT({} {})".format(longitude, latitude)

    @staticmethod
    def build_box_ewkt(latitude, longitude, half_grid):
        """Create an EWKT geometry string from latitude and longitude and half the grid size"""
        return "SRID=4326;POLYGON(({} {}, {} {}, {} {}, {} {}, {} {}))".format(
            longitude - half_grid,
            latitude - half_grid,
            longitude - half_grid,
            latitude + half_grid,
            longitude + half_grid,
            latitude + half_grid,
            longitude + half_grid,
            latitude - half_grid,
            longitude - half_grid,
            latitude - half_grid,
        )

    @staticmethod
    def build_entry(lat, lon, half_grid):
        """Create a SatelliteBox entry and return it"""
        return SatelliteBox(
            centroid=SatelliteBox.build_ewkt(lat, lon),
            geom=SatelliteBox.build_box_ewkt(lat, lon, half_grid),
        )


class SatelliteGrid(Base):
    """Locations of the discretised satellite locations"""

    __tablename__ = "satellite_grid"
    __table_args__ = {"schema": "interest_points"}

    point_id = Column(
        UUID,
        ForeignKey("interest_points.meta_point.id"),
        primary_key=True,
        nullable=False,
    )
    box_id = Column(
        UUID,
        ForeignKey("interest_points.satellite_box.id"),
        primary_key=True,
        nullable=False,
    )

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<SatelliteGrid(" + ", ".join(vals)

    @staticmethod
    def build_entry(point_id, box_id):
        """Create a SatelliteGrid entry and return it"""
        return SatelliteGrid(point_id=point_id, box_id=box_id)


class SatelliteForecast(Base):
    """Table of Satellite forecasts"""

    __tablename__ = "satellite_forecast"
    __table_args__ = {"schema": "dynamic_data"}

    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    box_id = Column(
        UUID,
        ForeignKey("interest_points.satellite_box.id"),
        primary_key=True,
        nullable=False,
    )
    species_code = Column(String(4), primary_key=True, nullable=False)
    value = Column(DOUBLE_PRECISION, nullable=True)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<SatelliteForecast(" + ", ".join(vals) + ")>"
