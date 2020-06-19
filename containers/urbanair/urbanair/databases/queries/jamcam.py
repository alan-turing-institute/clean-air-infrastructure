"""Jamcam database queries and external api calls"""
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session, Query
from geojson import Feature, Point, FeatureCollection
import requests
from cleanair.databases.tables import JamCamVideoStats
from cleanair.decorators import db_query
from ...types import DetectionClass

TWELVE_HOUR_INTERVAL = text("interval '12 hour'")
ONE_HOUR_INTERVAL = text("interval '1 hour'")


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


@db_query
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

    if camera_id:
        res = res.filter(JamCamVideoStats.camera_id == camera_id + ".mp4")

    # Filter by time
    if starttime:
        res = res.filter(
            JamCamVideoStats.video_upload_datetime >= starttime.isoformat(),
        )
    if endtime:
        res = res.filter(JamCamVideoStats.video_upload_datetime < endtime.isoformat(),)

    # Filter by detection class
    if detection_class.value != "all":
        res = res.filter(
            JamCamVideoStats.detection_class
            == DetectionClass.map_detection_class(detection_class)
        )

    return res


@db_query
def get_jamcam_recent(
    db: Session,
    camera_id: Optional[str],
    detection_class: DetectionClass = DetectionClass.all_classes,
    starttime: Optional[datetime] = None,
    endtime: Optional[datetime] = None,
) -> Query:
    """Get jamcam counts"""
    max_video_upload_datetime = db.query(
        func.max(JamCamVideoStats.video_upload_datetime).label(
            "max_video_upload_datetime"
        )
    ).subquery()

    res = db.query(
        func.split_part(JamCamVideoStats.camera_id, ".mp4", 1).label("camera_id"),
        JamCamVideoStats.counts,
        JamCamVideoStats.detection_class,
        JamCamVideoStats.video_upload_datetime.label("measurement_start_utc"),
    )

    if camera_id:
        res = res.filter(JamCamVideoStats.camera_id == camera_id + ".mp4")

    # Filter by time
    if starttime and endtime:
        res = res.filter(
            JamCamVideoStats.video_upload_datetime < endtime.isoformat(),
            JamCamVideoStats.video_upload_datetime >= starttime.isoformat(),
        )
    elif (not endtime) and (not starttime):
        res = res.filter(
            JamCamVideoStats.video_upload_datetime
            > max_video_upload_datetime.c.max_video_upload_datetime
            - TWELVE_HOUR_INTERVAL
        )
    else:
        return None

    # Filter by detection class
    if detection_class.value != "all":
        res = res.filter(
            JamCamVideoStats.detection_class
            == DetectionClass.map_detection_class(detection_class)
        )

    return res


@db_query
def get_jamcam_snapshot(
    db: Session,
    camera_id: Optional[str],
    detection_class: DetectionClass = DetectionClass.all_classes,
    starttime: Optional[datetime] = None,
    endtime: Optional[datetime] = None,
) -> Query:
    """Get hourly aggregates"""

    max_video_upload_datetime = db.query(
        func.max(JamCamVideoStats.video_upload_datetime).label(
            "max_video_upload_datetime"
        )
    ).subquery()

    res = db.query(
        func.split_part(JamCamVideoStats.camera_id, ".mp4", 1).label("camera_id"),
        func.sum(JamCamVideoStats.counts).label("counts"),
        JamCamVideoStats.detection_class,
        func.date_trunc("hour", JamCamVideoStats.video_upload_datetime).label(
            "measurement_start_utc"
        ),
    ).group_by(
        func.date_trunc("hour", JamCamVideoStats.video_upload_datetime),
        JamCamVideoStats.camera_id,
        JamCamVideoStats.detection_class,
    )

    # Filter by time
    if starttime and endtime:
        res = res.filter(
            JamCamVideoStats.video_upload_datetime < endtime.isoformat(),
            JamCamVideoStats.video_upload_datetime >= starttime.isoformat(),
        )
    elif (not endtime) and (not starttime):
        res = res.filter(
            func.date_trunc("hour", JamCamVideoStats.video_upload_datetime)
            > func.date_trunc(
                "hour", max_video_upload_datetime.c.max_video_upload_datetime
            )
            - ONE_HOUR_INTERVAL
        )
    else:
        return None

    # Filter by detection class
    if detection_class.value != "all":
        res = res.filter(
            JamCamVideoStats.detection_class
            == DetectionClass.map_detection_class(detection_class)
        )

    return res
