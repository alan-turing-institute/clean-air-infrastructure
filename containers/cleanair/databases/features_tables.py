"""
Tables for intersection between datasource and interest points
"""

from sqlalchemy import Column, ForeignKey, String, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from . import Base


class features_UKMAP(Base):
    """Intersection between interest points and UKMap"""
    __tablename__ = "features_ukmap"
    __table_args__ = {'schema': 'buffers'}

    point_id = Column(UUID,  primary_key=True, nullable=False)
    source = Column(String(7))

    # geom_1000 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    # geom_500 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    # geom_200 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    # geom_100 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    # geom_10 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))

    total_museum_area_500 = Column(Float(), nullable = False)
    total_hospital_area_500 = Column(Float(), nullable = False)
    total_grass_area_500 = Column(Float(), nullable = False)
    total_park_area500 = Column(Float(), nullable = False)
    total_water_area_500 = Column(Float(), nullable = False)
    total_flat_area_500 = Column(Float(), nullable = False)
    max_building_height_500 = Column(Float(), nullable = False)
    total_museum_area_200 = Column(Float(), nullable = False)
    total_hospital_area_200 = Column(Float(), nullable = False)
    total_grass_area_200 = Column(Float(), nullable = False)
    total_park_area200 = Column(Float(), nullable = False)
    total_water_area_200 = Column(Float(), nullable = False)
    total_flat_area_200 = Column(Float(), nullable = False)
    max_building_height_200 = Column(Float(), nullable = False)
    total_museum_area_1000 = Column(Float(), nullable = False)
    total_hospital_area_1000 = Column(Float(), nullable = False)
    total_grass_area_1000 = Column(Float(), nullable = False)
    total_park_area1000 = Column(Float(), nullable = False)
    total_water_area_1000 = Column(Float(), nullable = False)
    total_flat_area_1000 = Column(Float(), nullable = False)
    max_building_height_1000 = Column(Float(), nullable = False)
    total_museum_area_100 = Column(Float(), nullable = False)
    total_hospital_area_100 = Column(Float(), nullable = False)
    total_grass_area_100 = Column(Float(), nullable = False)
    total_park_area100 = Column(Float(), nullable = False)
    total_water_area_100 = Column(Float(), nullable = False)
    total_flat_area_100 = Column(Float(), nullable = False)
    max_building_height_100 = Column(Float(), nullable = False)
    total_museum_area_10 = Column(Float(), nullable = False)
    total_hospital_area_10 = Column(Float(), nullable = False)
    total_grass_area_10 = Column(Float(), nullable = False)
    total_park_area10 = Column(Float(), nullable = False)
    total_water_area_10 = Column(Float(), nullable = False)
    total_flat_area_10 = Column(Float(), nullable = False)
    max_building_height_10 = Column(Float(), nullable = False)