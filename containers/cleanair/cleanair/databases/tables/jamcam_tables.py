"""Tables for jamcam results"""
from geoalchemy2 import Geometry
from sqlalchemy import Column, String, BigInteger, Text
from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import (
    TIMESTAMP,
    DATE,
    SMALLINT,
    REAL,
    VARCHAR,
)

from ..base import Base


class JamCamFrameStats(Base):
    """Table of detection events"""

    __tablename__ = "frame_stats_v4"
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
    location = Column(Geometry(geometry_type="POINT"))
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

    __tablename__ = "video_stats_v4"
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

    Index("date_detection_class_idx", "date", "detection_class")

    __tablename__ = "day_stats_v3"
    __table_args__ = {"schema": "jamcam"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(VARCHAR(20), nullable=True)
    date = Column(DATE, nullable=True)
    detection_class = Column(String(20), nullable=True)
    count = Column(REAL, nullable=True)
    source = Column(SMALLINT, nullable=False)

    UniqueConstraint(camera_id, date, detection_class)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamDayStats(" + ", ".join(vals) + ")>"


class JamCamMetaData(Base):
    """Table of Jamcam data: locations, flags, etc."""

    # pylint: disable=C0103

    __tablename__ = "metadata"
    __table_args__ = {"schema": "jamcam"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(VARCHAR(20))
    location = Column(Geometry(geometry_type="POINT"))
    notes = Column(VARCHAR(128))
    u0 = Column(SMALLINT)
    v0 = Column(SMALLINT)
    u1 = Column(SMALLINT)
    h = Column(REAL)
    translation_x = Column(REAL)
    translation_y = Column(REAL)
    rotation = Column(REAL)
    scale_x = Column(REAL)
    scale_y = Column(REAL)
    shear_x = Column(REAL)
    shear_y = Column(REAL)
    flag = Column(SMALLINT)
    borough_name = Column(VARCHAR)
    borough_gss_code = Column(VARCHAR)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamMetaData(" + ", ".join(vals) + ")>"
