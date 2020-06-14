from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from cleanair.databases.tables import JamCamVideoStats
from ..databases import get_db
from ..databases import schemas

router = APIRouter()


@router.get("/recent", response_model=List[schemas.JamCamVideo])
async def cam_recent(
    id: str, starttime: datetime, endtime: datetime, db: Session = Depends(get_db),
):

    max_video_upload_datetime = db.query(
        func.max(JamCamVideoStats.video_upload_datetime).label(
            "max_video_upload_datetime"
        )
    ).subquery()

    res = db.query(
        JamCamVideoStats.counts,
        JamCamVideoStats.detection_class,
        JamCamVideoStats.creation_datetime,
    ).filter(
        JamCamVideoStats.camera_id == id_ + ".mp4",
        JamCamVideoStats.video_upload_datetime
        > max_video_upload_datetime.c.max_video_upload_datetime - TWELVE_HOUR_INTERVAL,
    )

    if starttime:
        res = res.filter(JamCamVideoStats.creation_datetime >= starttime)
    if endtime:
        res = res.filter(JamCamVideoStats.creation_datetime < endtime)

    return res.order_by(JamCamVideoStats.creation_datetime).all()


@router.get("/snapshot")
async def cam_snapshot(id: str):
    return
