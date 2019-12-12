"""
Tables for intersection between datasource and interest points
"""
from sqlalchemy import Column, ForeignKey, String, Float
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from ..base import Base


class IntersectionGeom(Base):
    """Intersection between interest points and UKMap as geometries"""
    __tablename__ = "intersection_geom"
    __table_args__ = {"schema": "static_features"}

    point_id = Column(UUID, ForeignKey("interest_points.meta_point.id"), primary_key=True, nullable=False)
    feature_name = Column(String(50), primary_key=True, nullable=False)
    geom_1000 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_500 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_200 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_100 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))
    geom_10 = Column(Geometry(geometry_type="GEOMETRYCOLLECTION", srid=4326, dimension=2, spatial_index=True))

    # Create IntersectionGeom.point with no reverse relationship
    point = relationship("MetaPoint")

    def __repr__(self):
        return "<IntersectionGeom(" + ", ".join([
            "point_id='{}'".format(self.point_id),
            "feature_name='{}'".format(self.feature_name),
            "geom_1000='{}'".format(self.geom_1000),
            "geom_500='{}'".format(self.geom_500),
            "geom_200='{}'".format(self.geom_200),
            "geom_100='{}'".format(self.geom_100),
            "geom_10='{}'".format(self.geom_10),
            ])

    @staticmethod
    def build_entry(feature_name, reading_tuple):
        """
        Create a IntersectionGeom entry and return it
        """
        return IntersectionGeom(point_id=str(reading_tuple[0]),
                                feature_name=feature_name,
                                geom_1000=reading_tuple[1],
                                geom_500=reading_tuple[2],
                                geom_200=reading_tuple[3],
                                geom_100=reading_tuple[4],
                                geom_10=reading_tuple[5])


class IntersectionValue(Base):
    """Intersection between interest points and UKMap as values"""
    __tablename__ = "intersection_value"
    __table_args__ = {"schema": "static_features"}

    point_id = Column(UUID, ForeignKey("interest_points.meta_point.id"), primary_key=True, nullable=False)
    feature_name = Column(String(50), primary_key=True, nullable=False)
    value_1000 = Column(Float)
    value_500 = Column(Float)
    value_200 = Column(Float)
    value_100 = Column(Float)
    value_10 = Column(Float)

    # Create IntersectionValue.point with no reverse relationship
    point = relationship("MetaPoint")

    def __repr__(self):
        return "<IntersectionValue(" + ", ".join([
            "point_id='{}'".format(self.point_id),
            "feature_name='{}'".format(self.feature_name),
            "value_1000='{}'".format(self.value_1000),
            "value_500='{}'".format(self.value_500),
            "value_200='{}'".format(self.value_200),
            "value_100='{}'".format(self.value_100),
            "value_10='{}'".format(self.value_10),
            ])

    @staticmethod
    def build_entry(feature_name, reading_tuple):
        """
        Create a IntersectionValue entry and return it
        """
        return IntersectionValue(point_id=str(reading_tuple[0]),
                                 feature_name=feature_name,
                                 value_1000=reading_tuple[1],
                                 value_500=reading_tuple[2],
                                 value_200=reading_tuple[3],
                                 value_100=reading_tuple[4],
                                 value_10=reading_tuple[5])

class IntersectionValueDynamic(Base):
    """Intersection between interest points and UKMap as values"""
    __tablename__ = "intersection_value_dynamic"
    __table_args__ = {"schema": "static_features"}

    point_id = Column(UUID, ForeignKey("interest_points.meta_point.id"), primary_key=True, nullable=False)
    feature_name = Column(String(50), primary_key=True, nullable=False)
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    value_1000 = Column(Float)
    value_500 = Column(Float)
    value_200 = Column(Float)
    value_100 = Column(Float)
    value_10 = Column(Float)

    # Create IntersectionValue.point with no reverse relationship
    point = relationship("MetaPoint")

    def __repr__(self):
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in [c.name for c in self.__table__.columns]]
        return "<IntersectionValueDynamic(" + ", ".join(vals)

    @staticmethod
    def build_entry(feature_name, reading_tuple):
        """
        Create a IntersectionValue entry and return it
        """
        return IntersectionValue(point_id=str(reading_tuple[0]),
                                 feature_name=feature_name,
                                 value_1000=reading_tuple[1],
                                 value_500=reading_tuple[2],
                                 value_200=reading_tuple[3],
                                 value_100=reading_tuple[4],
                                 value_10=reading_tuple[5])
