"""
Tables for intersection between datasource and interest points
"""
from sqlalchemy import Column, ForeignKey, String, Float, Index
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from ..base import Base


class IntersectionValue(Base):
    """Intersection between interest points and UKMap as values"""

    __tablename__ = "intersection_value2"
    __table_args__ = (
        Index("intersection_value_id_name_idx", "point_id", "feature_name"),
        {"schema": "static_features"},
    )

    point_id = Column(
        UUID,
        ForeignKey("interest_points.meta_point.id"),
        primary_key=True,
        nullable=False,
    )
    feature_name = Column(String(50), primary_key=True, nullable=False)
    value_1000 = Column(Float, nullable=False)
    value_500 = Column(Float, nullable=False)
    value_200 = Column(Float, nullable=False)
    value_100 = Column(Float, nullable=False)
    value_10 = Column(Float, nullable=False)

    # Create IntersectionValue.point with no reverse relationship
    point = relationship("MetaPoint")

    def __repr__(self):
        return "<IntersectionValue(" + ", ".join(
            [
                "point_id='{}'".format(self.point_id),
                "feature_name='{}'".format(self.feature_name),
                "value_1000='{}'".format(self.value_1000),
                "value_500='{}'".format(self.value_500),
                "value_200='{}'".format(self.value_200),
                "value_100='{}'".format(self.value_100),
                "value_10='{}'".format(self.value_10),
            ]
        )

    @staticmethod
    def build_entry(feature_name, reading_tuple):
        """
        Create a IntersectionValue entry and return it
        """
        return IntersectionValue(
            point_id=str(reading_tuple[0]),
            feature_name=feature_name,
            value_1000=reading_tuple[1],
            value_500=reading_tuple[2],
            value_200=reading_tuple[3],
            value_100=reading_tuple[4],
            value_10=reading_tuple[5],
        )


class IntersectionValueDynamic(Base):
    """Intersection between interest points and UKMap as values"""

    __tablename__ = "intersection_value_dynamic"
    __table_args__ = {"schema": "dynamic_features"}

    point_id = Column(
        UUID,
        ForeignKey("interest_points.meta_point.id"),
        primary_key=True,
        nullable=False,
    )
    feature_name = Column(String(50), primary_key=True, nullable=False)
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    value_1000 = Column(Float, nullable=False)
    value_500 = Column(Float, nullable=False)
    value_200 = Column(Float, nullable=False)
    value_100 = Column(Float, nullable=False)
    value_10 = Column(Float, nullable=False)

    # Create IntersectionValue.point with no reverse relationship
    point = relationship("MetaPoint")

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<IntersectionValueDynamic(" + ", ".join(vals)

    @staticmethod
    def build_entry(feature_name, reading_tuple):
        """
        Create a IntersectionValue entry and return it
        """
        return IntersectionValue(
            point_id=str(reading_tuple[0]),
            feature_name=feature_name,
            value_1000=reading_tuple[1],
            value_500=reading_tuple[2],
            value_200=reading_tuple[3],
            value_100=reading_tuple[4],
            value_10=reading_tuple[5],
        )
