from fastapi import APIRouter, Depends
from typing import List
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..databases import get_db
from ..databases.schemas.jamcam import JamCamVideo, JamCamBase
from ..databases.queries.jamcam import get_jamcam_recent
from ..types import DetectionClass

router = APIRouter()


@router.get("/recent", response_model=List[JamCamVideo])
async def cam_recent(
    camera_id: str = None,
    detection_class: DetectionClass = DetectionClass.all_classes,
    starttime: datetime = None,
    endtime: datetime = None,
    db: Session = Depends(get_db),
):
    return get_jamcam_recent(db, camera_id, detection_class, starttime, endtime).all()


@router.get("/snapshot", response_model=List[JamCamBase])
async def cam_snapshot(
    detection_class: DetectionClass = DetectionClass.all_classes,
    db: Session = Depends(get_db),
):

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
