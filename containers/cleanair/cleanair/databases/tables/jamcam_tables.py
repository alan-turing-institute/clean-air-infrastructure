"""Tables for jamcam results"""
from sqlalchemy import Column, String, BigInteger, REAL, BOOLEAN
from sqlalchemy.dialects.postgresql import TIMESTAMP, SMALLINT, REAL, VARCHAR
from geoalchemy2 import Geometry
from ..base import Base


class JamCamFrameStats(Base):
    """Table of JamCam Frame stats"""

    __tablename__ = "frame_stats_v2"
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

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamFrameStats(" + ", ".join(vals) + ")>"


class JamCamVideoStats(Base):
    """Table of JamCam Video stats"""

    __tablename__ = "video_stats_v2"
    __table_args__ = {"schema": "jamcam"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(VARCHAR(20))
    video_upload_datetime = Column(TIMESTAMP)
    detection_class = Column(String(20))
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


class JamCamMetaData(Base):
    """JamCam Metadata table"""

    __tablename__ = "metadata"
    __table_args__ = {"schema": "jamcam"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(VARCHAR(20), nullable=False)
    location = Column(
        Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True,),
        nullable=False,
    )
    notes = Column(VARCHAR(128))
    u0 = Column(SMALLINT)
    v0 = Column(SMALLINT)
    u1 = Column(SMALLINT)
    h = Column(REAL)
    flag = Column(SMALLINT)
