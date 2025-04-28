"""
Table for storing mapping of interset points to road segments
"""
from sqlalchemy import Column, ForeignKey, PrimaryKeyConstraint, Index, Float, DateTime

from ..base import Base


class PointRoadMap(Base):
    """Table of road segments mapped to interest points"""

    __tablename__ = "point_road_map"
    __table_args__ = {"schema": "interest_points"}

    point_id = Column(ForeignKey("interest_points.meta_point.id"))
    road_segment_id = Column(ForeignKey("static_data.oshighway_roadlink.toid"))
    buffer_radius = Column(Float)
    map_datetime = Column(DateTime)

    road_point_pk = PrimaryKeyConstraint(point_id, road_segment_id, buffer_radius)
    point_index = Index(point_id)


    def __repr__(self):
        return f"<RoadPointMap( point_id: {self.point_id}," \
               f" road_segment_id: {self.road_segment_id}," \
               f" buffer_radius: {self.buffer_radius}" \
               f" map_datetime: {self.map_datetime}" \
               f")>"
