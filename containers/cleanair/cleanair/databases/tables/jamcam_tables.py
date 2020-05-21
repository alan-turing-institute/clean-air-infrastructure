"""Tables for jamcam results"""
from sqlalchemy import Column, ForeignKey, String, Integer, Enum
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, BOOLEAN, SMALLINT, REAL
from ..base import Base

class JamCamFrameStats(Base):
    """Table of LAQN sites"""

    __tablename__ = "frame_stats_v2"
    __table_args__ = {"schema": "jamcam"}

    camera_id = Column(String(20))
    video_upload_datetime = Column(TIMESTAMP)
    frame_id = Column(SMALLINT)
    vehicle_id = Column(SMALLINT)
    vehicle_type = Column(String(20))
    confidence = Column(REAL)
    box_x = Column(SMALLINT)
    box_w = Column(SMALLINT)
    box_h = Column(SMALLINT)
    creation_datetime = Column(TIMESTAMP)


    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamFrameStats(" + ", ".join(vals) + ")>"

class JamCamVideoStats(Base):
    """Table of LAQN sites"""

    __tablename__ = "video_stats_v2"
    __table_args__ = {"schema": "jamcam"}

    camera_id = Column(VARCHAR(20))
    video_upload_datetime = Column(TIMESTAMP)
    vehicle_type = Column(VARCHAR(20))
    counts = Column(REAL)
    stops = Column(REAL)
    starts = Column(REAL)
    creation_datetime = Column(TIMESTAMP)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamFrameStats(" + ", ".join(vals) + ")>"
