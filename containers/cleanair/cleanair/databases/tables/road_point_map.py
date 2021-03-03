"""
Table for storing mapping of interset points to road segments
"""
from sqlalchemy import Column, ForeignKey, Float

from ..base import Base


class RoadPointMap(Base):
    """Table of road segments mapped to interest points"""

    __tablename__ = "road_point_map"
    __table_args__ = {"schema": "interest_points"}

    point_id = Column(ForeignKey("interest_points.meta_point.id"))
    road_segment_id = Column(ForeignKey("static_data.oshighway_roadlink.toid"))
    buffer_radius = Column(Float)


    def __repr__(self):
        return f"<RoadPointMap( point_id: {self.point_id}," \
               f" road_segment_id: {self.road_segment_id}," \
               f" buffer_radius: {self.buffer_radius}" \
               f")>"
