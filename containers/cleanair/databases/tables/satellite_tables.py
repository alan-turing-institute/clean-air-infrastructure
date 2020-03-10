"""
Tables for Satellite data
"""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID, INTEGER
from geoalchemy2 import Geometry
from ..base import Base


class SatelliteSite(Base):
    """Locations of the discretised satellite locations"""

    __tablename__ = "satellite_site"
    __table_args__ = {"schema": "interest_points"}

    box_id = Column(INTEGER, nullable=False, primary_key=True, autoincrement=True)
    location = Column(
        Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True), primary_key=True
    )
    geom = Column(
        Geometry(geometry_type="POLYGON", srid=4326, dimension=2, spatial_index=True)
    )

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<SatelliteSite(" + ", ".join(vals)

    @staticmethod
    def build_location_ewkt(latitude, longitude):
        """Create an EWKT geometry string from latitude and longitude"""
        return "SRID=4326;POINT({} {})".format(longitude, latitude)

    @staticmethod
    def build_box_ewkt(latitude, longitude, half_gridsize):
        """Create an EWKT geometry string from latitude and longitude and half_gridsize"""
        corners = [
            [latitude - half_gridsize, longitude - half_gridsize],
            [latitude - half_gridsize, longitude + half_gridsize],
            [latitude + half_gridsize, longitude + half_gridsize],
            [latitude + half_gridsize, longitude - half_gridsize],
            [latitude - half_gridsize, longitude - half_gridsize],
        ]
        coord_strings = "".join(["{} {},".format(i[1], i[0]) for i in corners])[:-1]
        return "SRID=4326;POLYGON(({}))".format(coord_strings)

    @staticmethod
    def build_entry(lat, lon, half_gridsize, **kwargs):
        """Create a SatelliteSite entry and return it"""
        return SatelliteSite(
            location=SatelliteSite.build_location_ewkt(lat, lon),
            geom=SatelliteSite.build_box_ewkt(lat, lon, half_gridsize),
        )


class SatelliteDiscreteSite(Base):
    """Locations of the descritised satellite locations"""

    __tablename__ = "satellite_discrete_site"
    __table_args__ = {"schema": "interest_points"}

    point_id = Column(
        UUID,
        ForeignKey("interest_points.meta_point.id"),
        nullable=False,
        primary_key=True,
    )
    box_id = Column(
        INTEGER,
        ForeignKey("interest_points.satellite_site.box_id"),
        nullable=False,
        primary_key=True,
    )

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<SatelliteDiscreteSite(" + ", ".join(vals)


class SatelliteForecastReading(Base):
    """Table of Satellite readings"""

    __tablename__ = "satellite_forecast"
    __table_args__ = {"schema": "dynamic_data"}

    reference_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    box_id = Column(
        INTEGER,
        ForeignKey("interest_points.satellite_site.box_id"),
        primary_key=True,
        nullable=False,
    )
    species_code = Column(String(4), primary_key=True, nullable=False)
    value = Column(DOUBLE_PRECISION, nullable=True)
