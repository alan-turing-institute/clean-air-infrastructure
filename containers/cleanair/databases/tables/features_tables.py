"""
Tables for intersection between datasource and interest points
"""
from sqlalchemy import Column, ForeignKey, String, Integer, Float
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ..base import Base


class UKMapIntersectionGeoms(Base):
    """Intersection between interest points and UKMap as geometries"""
    __tablename__ = "ukmap_intersection_geoms"
    __table_args__ = {'schema': 'buffers'}

    point_id = Column(UUID, ForeignKey('buffers.interest_points.point_id'), primary_key=True, nullable=False)
    feature_type = Column(String(20), primary_key=True, nullable=False)
    geom_1000 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_500 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_200 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_100 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_10 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))

    def __repr__(self):
        return "<UKMapIntersectionGeoms(" + ", ".join([
               "point_id='{}'".format(self.point_id),
               "feature_type='{}'".format(self.feature_type),
               "geom_1000='{}'".format(self.geom_1000),
               "geom_500='{}'".format(self.geom_500),
               "geom_200='{}'".format(self.geom_200),
               "geom_100='{}'".format(self.geom_100),
               "geom_10='{}'".format(self.geom_10),
            ])

    @staticmethod
    def build_entry(feature_type, reading_tuple):
        """
        Create a UKMapIntersectionGeoms entry and return it
        """
        return UKMapIntersectionGeoms(point_id=str(reading_tuple[0]),
                                      feature_type=feature_type,
                                      geom_1000=reading_tuple[1],
                                      geom_500=reading_tuple[2],
                                      geom_200=reading_tuple[3],
                                      geom_100=reading_tuple[4],
                                      geom_10=reading_tuple[5])

class UKMapIntersectionValues(Base):
    """Intersection between interest points and UKMap as values"""
    __tablename__ = "ukmap_intersection_values"
    __table_args__ = {'schema': 'buffers'}

    point_id = Column(UUID, ForeignKey('buffers.interest_points.point_id'), primary_key=True, nullable=False)
    feature_type = Column(String(20), primary_key=True, nullable=False)
    value_1000 = Column(DOUBLE_PRECISION, nullable=False)
    value_500 = Column(DOUBLE_PRECISION, nullable=False)
    value_200 = Column(DOUBLE_PRECISION, nullable=False)
    value_100 = Column(DOUBLE_PRECISION, nullable=False)
    value_10 = Column(DOUBLE_PRECISION, nullable=False)

    def __repr__(self):
        return "<UKMapIntersectionValues(" + ", ".join([
               "point_id='{}'".format(self.point_id),
               "feature_type='{}'".format(self.feature_type),
               "value_1000='{}'".format(self.value_1000),
               "value_500='{}'".format(self.value_500),
               "value_200='{}'".format(self.value_200),
               "value_100='{}'".format(self.value_100),
               "value_10='{}'".format(self.value_10),
            ])

    @staticmethod
    def build_entry(feature_type, reading_tuple):
        """
        Create a UKMapIntersectionValues entry and return it
        """
        return UKMapIntersectionValues(point_id=str(reading_tuple[0]),
                                       feature_type=feature_type,
                                       value_1000=reading_tuple[1],
                                       value_500=reading_tuple[2],
                                       value_200=reading_tuple[3],
                                       value_100=reading_tuple[4],
                                       value_10=reading_tuple[5])






# class features_UKMAP(Base):
#     """Intersection between interest points and UKMap"""
#     __tablename__ = "features_ukmap"
#     __table_args__ = {'schema': 'buffers'}

#     point_id = Column(UUID, ForeignKey('buffers.interest_points.point_id'), primary_key=True, nullable=False)

#     # geom_1000 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
#     # geom_500 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
#     # geom_200 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
#     # geom_100 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
#     # geom_10 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))

#     total_museum_area_500 = Column(Float(), nullable = False)
#     total_hospital_area_500 = Column(Float(), nullable = False)
#     total_grass_area_500 = Column(Float(), nullable = False)
#     total_park_area500 = Column(Float(), nullable = False)
#     total_water_area_500 = Column(Float(), nullable = False)
#     total_flat_area_500 = Column(Float(), nullable = False)
#     max_building_height_500 = Column(Float(), nullable = False)
#     total_museum_area_200 = Column(Float(), nullable = False)
#     total_hospital_area_200 = Column(Float(), nullable = False)
#     total_grass_area_200 = Column(Float(), nullable = False)
#     total_park_area200 = Column(Float(), nullable = False)
#     total_water_area_200 = Column(Float(), nullable = False)
#     total_flat_area_200 = Column(Float(), nullable = False)
#     max_building_height_200 = Column(Float(), nullable = False)
#     total_museum_area_1000 = Column(Float(), nullable = False)
#     total_hospital_area_1000 = Column(Float(), nullable = False)
#     total_grass_area_1000 = Column(Float(), nullable = False)
#     total_park_area1000 = Column(Float(), nullable = False)
#     total_water_area_1000 = Column(Float(), nullable = False)
#     total_flat_area_1000 = Column(Float(), nullable = False)
#     max_building_height_1000 = Column(Float(), nullable = False)
#     total_museum_area_100 = Column(Float(), nullable = False)
#     total_hospital_area_100 = Column(Float(), nullable = False)
#     total_grass_area_100 = Column(Float(), nullable = False)
#     total_park_area100 = Column(Float(), nullable = False)
#     total_water_area_100 = Column(Float(), nullable = False)
#     total_flat_area_100 = Column(Float(), nullable = False)
#     max_building_height_100 = Column(Float(), nullable = False)
#     total_museum_area_10 = Column(Float(), nullable = False)
#     total_hospital_area_10 = Column(Float(), nullable = False)
#     total_grass_area_10 = Column(Float(), nullable = False)
#     total_park_area10 = Column(Float(), nullable = False)
#     total_water_area_10 = Column(Float(), nullable = False)
#     total_flat_area_10 = Column(Float(), nullable = False)
#     max_building_height_10 = Column(Float(), nullable = False)