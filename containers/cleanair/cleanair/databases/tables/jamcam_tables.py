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
    INTEGER,  # INT4
    FLOAT,  # FLOAT4
    BOOLEAN,  # BOOL
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
    """Table of Jamcam data: locations, flags, etc.
    # Current Jamcam meta table DDL
    # -----------------------------
    # CREATE TABLE jamcam.metadata (
    #     id bigserial NOT NULL,
    #     camera_id varchar(20) NOT NULL,
    #     "location" geometry(point, 4326) NOT NULL,
    #     notes varchar(128) NULL,
    #     u0 int2 NULL,
    #     v0 int2 NULL,
    #     u1 int2 NULL,
    #     h float4 NULL,
    #     flag int2 NULL,
    #     borough_name varchar NULL,
    #     borough_gss_code varchar NULL,
    #     translation_x float4 NULL,
    #     translation_y float4 NULL,
    #     rotation float4 NULL,
    #     scale_shear_x1 float4 NULL,
    #     scale_shear_x2 float4 NULL,
    #     scale_shear_y1 float4 NULL,
    #     scale_shear_y2 float4 NULL,
    #     focal_length float4 NULL,
    #     pitch float4 NULL,
    #     "scale" float4 NULL,
    #     CONSTRAINT metadata_pkey PRIMARY KEY (id)
    # );
    # CREATE INDEX idx_metadata_location ON jamcam.metadata USING gist (location);
    """

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
    flag = Column(SMALLINT)
    borough_name = Column(VARCHAR)
    borough_gss_code = Column(VARCHAR)
    translation_x = Column(FLOAT)
    translation_y = Column(FLOAT)
    rotation = Column(FLOAT)
    scale_shear_x1 = Column(FLOAT)
    scale_shear_x2 = Column(FLOAT)
    scale_shear_y1 = Column(FLOAT)
    scale_shear_y2 = Column(FLOAT)
    focal_length = Column(FLOAT)
    pitch = Column(FLOAT)
    scale = Column(FLOAT)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamMetaData(" + ", ".join(vals) + ")>"


class JamCamStabilitySummaryData(Base):
    """Table of Jamcam stability summary data
    # Current Jamcam Stability Summary table DDL
    # -----------------------------
    # CREATE TABLE jamcam.stability_summary (
    #     camera_id varchar NOT NULL,
    #     mean_ssim_avg0 float4 NULL,
    #     mean_mse_avg0 float4 NULL,
    #     var_ssim_avg0 float4 NULL,
    #     var_mse_avg0 float4 NULL,
    #     nocp_mse_avg0 int4 NULL,
    #     nocp_ssim_avg0 int4 NULL,
    #     score int4 NULL,
    #     CONSTRAINT stability_summary_pk PRIMARY KEY (camera_id)
    # );
    # CREATE INDEX stability_summary_camera_id_idx ON jamcam.stability_summary USING btree (camera_id);
    """

    # pylint: disable=C0103

    __tablename__ = "stability_summary"
    __table_args__ = {"schema": "jamcam"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(VARCHAR)
    mean_ssim_avg0 = Column(FLOAT)
    mean_mse_avg0 = Column(FLOAT)
    var_ssim_avg0 = Column(FLOAT)
    var_mse_avg0 = Column(FLOAT)
    nocp_mse_avg0 = Column(INTEGER)
    nocp_ssim_avg0 = Column(INTEGER)
    score = Column(INTEGER)

    Index("stability_summary_camera_id_idx", "camera_id")

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamStabilitySummaryData(" + ", ".join(vals) + ")>"


class JamCamStabilityRawData(Base):
    """Table of Jamcam stability raw data
    # Current Jamcam Stability Raw table DDL
    # -----------------------------
    # CREATE TABLE jamcam.stability_raw (
    #     camera_id varchar NOT NULL,
    #     mse_diff_n1 float4 NULL,
    #     mse_diff_0 float4 NULL,
    #     mse_diff_avg0 float4 NULL,
    #     ssim_diff_n1 float4 NULL,
    #     ssim_diff_0 float4 NULL,
    #     ssim_diff_avg0 float4 NULL,
    #     "date" date NULL
    # );
    # CREATE UNIQUE INDEX stability_raw_camera_id_idx ON jamcam.stability_raw USING btree (camera_id, date);
    """

    # pylint: disable=C0103

    __tablename__ = "stability_raw"
    __table_args__ = {"schema": "jamcam"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(VARCHAR)
    mse_diff_n1 = Column(FLOAT)
    mse_diff_0 = Column(FLOAT)
    mse_diff_avg0 = Column(FLOAT)
    ssim_diff_n1 = Column(FLOAT)
    ssim_diff_0 = Column(FLOAT)
    ssim_diff_avg0 = Column(FLOAT)
    date = Column(DATE)
    is_cp = Column(BOOLEAN)

    Index("stability_raw_camera_id_idx", "camera_id", "date")
    UniqueConstraint(camera_id, date)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamStabilityRawData(" + ", ".join(vals) + ")>"


class JamCamConfidentDetections(Base):
    """Table of Jamcam confident detections data
    # Current Jamcam Confident Detections table DDL
    # -----------------------------
    # CREATE MATERIALIZED VIEW jamcam.video_summary_80perc
    # TABLESPACE pg_default
    # AS SELECT frame_stats_v3.camera_id,
    #     frame_stats_v3.video_upload_datetime,
    #     frame_stats_v3.detection_class,
    #     max(frame_stats_v3.detection_id) AS count
    # FROM jamcam.frame_stats_v3
    # WHERE frame_stats_v3.confidence > 0.8::double precision
    # GROUP BY frame_stats_v3.camera_id, frame_stats_v3.video_upload_datetime, frame_stats_v3.detection_class
    # WITH DATA;

    # -- View indexes:
    # CREATE INDEX video_summary_80perc_camera_id_idx ON jamcam.video_summary_80perc USING btree (camera_id, video_upload_datetime);
    """

    # pylint: disable=C0103

    __tablename__ = "video_summary_80perc"
    __table_args__ = {"schema": "jamcam"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    camera_id = Column(VARCHAR)
    video_upload_datetime = Column(DATE)
    count = Column(SMALLINT)
    detection_class = Column(String(20))

    Index("video_summary_80perc_camera_id_idx", "camera_id", "date")
    UniqueConstraint(camera_id, video_upload_datetime)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<JamCamConfidentDetections(" + ", ".join(vals) + ")>"