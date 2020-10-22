"""Jamcam database queries and external api calls"""
from datetime import datetime, timedelta, date
from typing import Optional

import requests
from cleanair.databases.materialised_views.jamcam_today_stats_view import (
    JamcamTodayStatsView,
)
from cleanair.databases.tables import JamCamDayStats
from cleanair.databases.tables import JamCamVideoStats, JamCamMetaData
from cleanair.decorators import db_query
from fastapi import HTTPException
from geojson import Feature, Point, FeatureCollection
from sqlalchemy import func, text
from sqlalchemy.orm import Session, Query
from sqlalchemy.sql.selectable import Alias

from ...types import DetectionClass

# TWELVE_HOUR_INTERVAL = text("interval '12 hour'")
ONE_HOUR_INTERVAL = text("interval '1 hour'")


def start_end_filter(
    query: Query,
    starttime: Optional[datetime],
    endtime: Optional[datetime],
    max_video_upload_time_sq: Alias,
) -> Query:
    """Create an sqlalchemy filter which implements the following:
        If starttime and endtime are given filter between them.
        If only starttime filter 24 hours including starttime
        If only endtime  filter 24 hours proceeding endtime
        If not starttime and endtime get the last day of available data
    """

    if starttime and endtime:
        return query.filter(
            JamCamVideoStats.video_upload_datetime >= starttime,
            JamCamVideoStats.video_upload_datetime < endtime,
        )

    # 24 hours from starttime
    if starttime:
        return query.filter(
            JamCamVideoStats.video_upload_datetime >= starttime,
            JamCamVideoStats.video_upload_datetime < starttime + timedelta(hours=24),
        )

    # 24 hours before endtime
    if endtime:
        return query.filter(
            JamCamVideoStats.video_upload_datetime < endtime,
            JamCamVideoStats.video_upload_datetime >= endtime - timedelta(hours=24),
        )

    # Last available 24 hours
    return query.filter(
        JamCamVideoStats.video_upload_datetime
        >= func.date_trunc("day", max_video_upload_time_sq.c.max_video_upload_datetime)
    )


def detection_class_filter(query: Query, detection_class: DetectionClass) -> Query:
    """Filter by detection class. If detection_class == DetectionClass.all then filter
    by remaining detection class options
    """
    if detection_class == DetectionClass.all_classes:
        return query.filter(
            JamCamVideoStats.detection_class.in_(DetectionClass.map_all())
        )

    return query.filter(
        JamCamVideoStats.detection_class
        == DetectionClass.map_detection_class(detection_class)
    )


def camera_id_filter(query: Query, camera_id: Optional[str]) -> Query:
    "Filter by camera_id"
    if camera_id:
        return query.filter(JamCamVideoStats.camera_id == camera_id)
    return query


def max_video_upload_q(db: Session) -> Query:
    "Max video upload time"
    return db.query(
        func.max(JamCamVideoStats.video_upload_datetime).label(
            "max_video_upload_datetime"
        )
    )


def get_jamcam_info(
    jamcam_url: str = "https://api.tfl.gov.uk/Place/Type/JamCam/",
) -> FeatureCollection:
    "Request jamcam camera information and write to geoJSON"

    cam_req = requests.get(jamcam_url)
    if cam_req.status_code != 200:
        raise HTTPException(
            status_code=404,
            detail="Could not get jamcam info. Please contact API administrator",
        )

    cam_data = cam_req.json()

    output = list(
        map(
            lambda x: Feature(
                id=x["id"].split("_")[1],
                geometry=Point((x["lon"], x["lat"])),
                properties={"camera_id": x["id"].split("_")[1]},
            ),
            cam_data,
        )
    )

    out = FeatureCollection(output)

    return out


@db_query()
def get_jamcam_available(
    db: Session,
    camera_id: Optional[str],
    detection_class: DetectionClass = DetectionClass.all_classes,
    starttime: Optional[datetime] = None,
    endtime: Optional[datetime] = None,
) -> Query:
    """Get camera data availability"""

    agg_func = func.distinct(
        func.date_trunc("hour", JamCamVideoStats.video_upload_datetime).label(
            "measurement_start_utc"
        ),
    ).label("measurement_start_utc")

    res = db.query(agg_func).order_by(agg_func)

    # Filter by camera_id
    res = camera_id_filter(res, camera_id)

    # Filter by time
    if starttime:
        res = res.filter(JamCamVideoStats.video_upload_datetime >= starttime,)
    if endtime:
        res = res.filter(JamCamVideoStats.video_upload_datetime < endtime)

    # Filter by detection class
    res = detection_class_filter(res, detection_class)

    return res


@db_query()
def get_jamcam_raw(
    db: Session,
    camera_id: Optional[str],
    detection_class: DetectionClass = DetectionClass.all_classes,
    starttime: Optional[datetime] = None,
    endtime: Optional[datetime] = None,
) -> Query:
    """Get jamcam counts"""

    max_video_upload_datetime_sq = max_video_upload_q(db).subquery()

    res = db.query(
        JamCamVideoStats.camera_id,
        JamCamVideoStats.counts,
        JamCamVideoStats.detection_class,
        JamCamVideoStats.video_upload_datetime.label("measurement_start_utc"),
    ).order_by(JamCamVideoStats.camera_id, JamCamVideoStats.video_upload_datetime)

    # Filter by camera_id
    res = camera_id_filter(res, camera_id)

    # Filter by time
    res = start_end_filter(res, starttime, endtime, max_video_upload_datetime_sq)

    # Filter by detection class
    res = detection_class_filter(res, detection_class)

    return res


@db_query()
def get_jamcam_hourly(
    db: Session,
    camera_id: Optional[str],
    detection_class: DetectionClass = DetectionClass.all_classes,
    starttime: Optional[datetime] = None,
    endtime: Optional[datetime] = None,
) -> Query:
    """Get hourly aggregates"""

    max_video_upload_datetime_sq = max_video_upload_q(db).subquery()

    res = (
        db.query(
            JamCamVideoStats.camera_id,
            func.avg(JamCamVideoStats.counts).label("counts"),
            JamCamVideoStats.detection_class,
            func.date_trunc("hour", JamCamVideoStats.video_upload_datetime).label(
                "measurement_start_utc"
            ),
        )
        .group_by(
            func.date_trunc("hour", JamCamVideoStats.video_upload_datetime),
            JamCamVideoStats.camera_id,
            JamCamVideoStats.detection_class,
        )
        .order_by(
            JamCamVideoStats.camera_id,
            func.date_trunc("hour", JamCamVideoStats.video_upload_datetime),
        )
    )

    # Filter by camera_id
    res = camera_id_filter(res, camera_id)

    # Filter by time
    res = start_end_filter(res, starttime, endtime, max_video_upload_datetime_sq)

    # Filter by detection class
    res = detection_class_filter(res, detection_class)

    return res


@db_query()
def get_jamcam_daily(
    db: Session,
    camera_id: Optional[str],
    detection_class: DetectionClass = DetectionClass.all_classes,
    day: Optional[date] = None,
) -> Query:
    """Get daily hourly average count"""

    query = db.query(
        JamCamDayStats.camera_id.label("camera_id"),
        JamCamDayStats.count.label("counts"),
        JamCamDayStats.detection_class.label("detection_class"),
    )

    query = query.filter(
        JamCamDayStats.detection_class
        == DetectionClass.map_detection_class(detection_class)
    )

    if camera_id:
        query = query.filter(JamCamDayStats.camera_id == camera_id)

    if date:
        query = query.filter(JamCamDayStats.date == day)

    return query


@db_query()
def get_jamcam_today(
    db: Session,
    camera_id: Optional[str],
    detection_class: DetectionClass = DetectionClass.all_classes,
) -> Query:
    """Get daily hourly average count"""

    query = db.query(JamcamTodayStatsView)

    query = query.filter(
        JamCamDayStats.detection_class
        == DetectionClass.map_detection_class(detection_class)
    )

    if camera_id:
        query = query.filter(JamCamDayStats.camera_id == camera_id)

    return query


@db_query()
def get_jamcam_metadata(db: Session) -> Query:
    return db.query(
        JamCamMetaData.camera_id.label("id"),
        func.ST_Y(JamCamMetaData.location).label("lat"),
        func.ST_X(JamCamMetaData.location).label("lon"),
        JamCamMetaData.flag.label("flag"),
    )
