"""
Tables for intersection between datasource and interest points
"""
from sqlalchemy import Column, ForeignKey, String, Float, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from ..base import Base


class StaticFeature(Base):
    """Any model features that are static (and therefore do not need a start-time column)"""

    __tablename__ = "static_feature"
    __table_args__ = (
        Index("static_feature_id_idx2", "point_id"),
        Index("static_feature_name_idx2", "feature_name"),
        Index("static_feature_id_name_idx2", "point_id", "feature_name"),
        {"schema": "model_features"},
    )

    point_id = Column(
        UUID(as_uuid=True),
        ForeignKey("interest_points.meta_point.id"),
        primary_key=True,
        nullable=False,
    )
    feature_name = Column(String(50), primary_key=True, nullable=False)
    feature_source = Column(String(50), primary_key=True, nullable=False)
    value_1000 = Column(Float, nullable=False)
    value_500 = Column(Float, nullable=False)
    value_200 = Column(Float, nullable=False)
    value_100 = Column(Float, nullable=False)
    value_10 = Column(Float, nullable=False)

    # Create StaticFeature.point with no reverse relationship
    point = relationship("MetaPoint")

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<StaticFeature" + ", ".join(vals) + ")>"

    @staticmethod
    def build_entry(feature_name, feature_source, reading_tuple):
        """
        Create a StaticFeature entry and return it
        """
        return StaticFeature(
            point_id=str(reading_tuple[0]),
            feature_name=feature_name,
            feature_source=feature_source,
            value_1000=reading_tuple[1],
            value_500=reading_tuple[2],
            value_200=reading_tuple[3],
            value_100=reading_tuple[4],
            value_10=reading_tuple[5],
        )


class DynamicFeature(Base):
    """Any model features that vary over time (and therefore need a start-time column)"""

    __tablename__ = "dynamic_feature"
    __table_args__ = (
        Index(
            "dynamic_feature_id_time_name_idx",
            "point_id",
            "measurement_start_utc",
            "feature_name",
        ),
        {"schema": "model_features"},
    )

    point_id = Column(
        UUID,
        ForeignKey("interest_points.meta_point.id"),
        primary_key=True,
        nullable=False,
        index=True,
    )
    measurement_start_utc = Column(
        TIMESTAMP, primary_key=True, nullable=False, index=True
    )
    feature_name = Column(String(50), primary_key=True, nullable=False)
    value_1000 = Column(Float)
    value_500 = Column(Float)
    value_200 = Column(Float)
    value_100 = Column(Float)
    value_10 = Column(Float)
    value_const = Column(Float)

    # Create DynamicFeature.point with no reverse relationship
    point = relationship("MetaPoint")

    def __repr__(self):
        cols = [c.name for c in self.__table__.columns]
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<DynamicFeature(" + ", ".join(vals) + ")>"

    @staticmethod
    def build_entry(feature_name, reading_tuple):
        """
        Create a DynamicFeature entry and return it
        """
        return DynamicFeature(
            point_id=str(reading_tuple[0]),
            measurement_start_utc=str(reading_tuple[1]),
            feature_name=feature_name,
            value_1000=reading_tuple[2],
            value_500=reading_tuple[3],
            value_200=reading_tuple[4],
            value_100=reading_tuple[5],
            value_10=reading_tuple[6],
        )
