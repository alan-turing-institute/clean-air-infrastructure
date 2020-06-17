from fastapi import HTTPException
from typing import List, Optional, Dict
from pydantic import BaseModel
from sqlalchemy import func, text
from sqlalchemy.orm import Session, Query
from datetime import datetime
from geojson import Feature, Point, FeatureCollection
import requests
from cleanair.databases.tables import JamCamVideoStats
from cleanair.decorators import db_query
from ...types import DetectionClass

TWELVE_HOUR_INTERVAL = text("interval '12 hour'")


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
def get_jamcam_recent(
    db: Session,
    camera_id: Optional[str],
    detection_class: DetectionClass = DetectionClass.all_classes,
    starttime: Optional[datetime] = None,
    endtime: Optional[datetime] = None,
) -> Query:

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


def get_jamcam_snapshot(db: Session, detection_class: DetectionClass) -> List[Dict]:

    if detection_class == DetectionClass.person:
        res = db.execute(
            """select split_part(camera_id, '.mp4', 1) AS camera_id, sum_counts as counts from jamcam.sum_counts_last_hour_people"""
        )
    elif detection_class == DetectionClass.car:
        res = db.execute(
            "select split_part(camera_id, '.mp4', 1) AS camera_id, sum_counts as counts from jamcam.sum_counts_last_hour_cars"
        )
    elif detection_class == DetectionClass.bus:
        res = db.execute(
            "select split_part(camera_id, '.mp4', 1) AS camera_id, sum_counts as counts from jamcam.sum_counts_last_hour_buses"
        )
    elif detection_class == DetectionClass.truck:
        res = db.execute(
            "select split_part(camera_id, '.mp4', 1) AS camera_id, sum_counts as counts from jamcam.sum_counts_last_hour_trucks"
        )
    elif detection_class == DetectionClass.motorbike:
        res = db.execute(
            "select split_part(camera_id, '.mp4', 1) AS camera_id, sum_counts as counts from jamcam.sum_counts_last_hour_motorbikes"
        )
    else:
        res = db.execute(
            "select split_part(camera_id, '.mp4', 1) AS camera_id, sum_counts as counts from jamcam.sum_counts_last_hour"
        )

    return [dict(row) for row in res]
