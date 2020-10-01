"""Tables for jamcam results"""
from sqlalchemy import Column, String, BigInteger, Text, Integer, Date
from sqlalchemy.dialects.postgresql import (
    TIMESTAMP,
    SMALLINT,
    REAL,
    VARCHAR,
)
from ..base import Base


class JamCamFrameStats(Base):
    """Table of detection events"""

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
    """Table of detection counts"""

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


class JamCamDayStats(Base):
    """Table of detection counts"""

    __tablename__ = "day_stats"
    __table_args__ = {"schema": "jamcam"}

    id = Column(Integer, primary_key=True, autoincrement=True)  # TODO Fix types  >>>  these were set manually, not defined here, correct to follow other tables
    camera_id = Column(VARCHAR(20))
    date = Column(Date)
    detection_class = Column(String(20))
    count = Column(REAL)
    source = Column(SMALLINT, nullable=False)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamDayStats(" + ", ".join(vals) + ")>"
