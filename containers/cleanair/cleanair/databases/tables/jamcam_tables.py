"""Tables for jamcam results"""
from sqlalchemy import Column, String, BigInteger, Text
from sqlalchemy.dialects.postgresql import (
    TIMESTAMP,
    SMALLINT,
    REAL,
    VARCHAR,
)
from ..base import Base


class JamCamFrameStats(Base):
    """Table of LAQN sites"""

    __tablename__ = "frame_stats_v3"
    __table_args__ = {"schema": "jamcam"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(String(20))
    video_upload_datetime = Column(TIMESTAMP)
    frame_id = Column(SMALLINT)
    detection_id = Column(SMALLINT)
    detection_class = Column(String(20))
    confidence = Column(REAL)
    box_x = Column(SMALLINT)
    box_y = Column(SMALLINT)
    box_w = Column(SMALLINT)
    box_h = Column(SMALLINT)
    creation_datetime = Column(TIMESTAMP)
    source = Column(SMALLINT, default=1, nullable=False)
    filename = Column(Text())

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamFrameStats(" + ", ".join(vals) + ")>"


class JamCamVideoStats(Base):
    """Table of LAQN sites"""

    __tablename__ = "video_stats_v3"
    __table_args__ = {"schema": "jamcam"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(VARCHAR(20))
    video_upload_datetime = Column(TIMESTAMP, index=True)
    detection_class = Column(String(20))
    counts = Column(REAL)
    stops = Column(REAL)
    starts = Column(REAL)
    creation_datetime = Column(TIMESTAMP)
    source = Column(SMALLINT, default=1, nullable=False)
    filename = Column(Text())

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamVideoStats(" + ", ".join(vals) + ")>"
