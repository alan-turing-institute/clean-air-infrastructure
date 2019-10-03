"""
Tables for intersection between datasource and interest points
"""

from sqlalchemy import Column, ForeignKey, String, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from . import Base


class UKMapIntersections(Base):
    """Intersection between interest points and UKMap museums"""
    __tablename__ = "ukmap_intersections"
    __table_args__ = {'schema': 'buffers'}

    point_id = Column(UUID, ForeignKey('buffers.interest_points.point_id'), primary_key=True, nullable=False)
    feature_type = Column(String(20), nullable=False)
    geom_1000 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_500 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_200 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_100 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_10 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))

    def __repr__(self):
        return "<UKMapIntersections(" + ", ".join([
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
        Create a UKMapIntersections entry and return it
        """
        return UKMapIntersections(point_id=str(reading_tuple[0]),
                                  feature_type=feature_type,
                                  geom_1000=reading_tuple[1],
                                  geom_500=reading_tuple[2],
                                  geom_200=reading_tuple[3],
                                  geom_100=reading_tuple[4],
                                  geom_10=reading_tuple[5])

    # @staticmethod
    # def build_entry(feature_type, reading_tuple):
    #     """
    #     Create an UKMapIntersections entry, replacing empty strings with None
    #     """
    #     # Construct the record and return it
    #     return UKMapIntersections(point_id=str(reading_tuple[0]),
    #                               feature_type=feature_type,
    #                               geom=reading_tuple[1])


# class UKMapMuseums(Base):
#     """Intersection between interest points and UKMap museums"""
#     __tablename__ = "ukmap_museums"
#     __table_args__ = {'schema': 'buffers'}

#     point_id = Column(UUID, ForeignKey('buffers.interest_points.point_id'), primary_key=True, nullable=False)
#     geom_1000 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
#     geom_500 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
#     geom_200 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
#     geom_100 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
#     geom_10 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))

#     def __repr__(self):
#         return "<UKMapMuseums(" + ", ".join([
#             "point_id='{}'".format(self.point_id),
#             "geom_1000='{}'".format(self.geom_1000),
#             "geom_500='{}'".format(self.geom_500),
#             "geom_200='{}'".format(self.geom_200),
#             "geom_100='{}'".format(self.geom_100),
#             "geom_10='{}'".format(self.geom_10),
#             ])

#     @staticmethod
#     def build_entry(reading_tuple):
#         """
#         Create an UKMapMuseums entry, replacing empty strings with None
#         """

#         # Construct the record and return it
#         return UKMapMuseums(point_id=str(reading_tuple[0]),
#                             geom_1000=reading_tuple[1],
#                             geom_500=reading_tuple[2],
#                             geom_200=reading_tuple[3],
#                             geom_100=reading_tuple[4],
#                             geom_10=reading_tuple[5])



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