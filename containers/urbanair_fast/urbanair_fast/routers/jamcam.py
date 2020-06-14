from fastapi import APIRouter, Depends
from typing import List
from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Session
from ..databases import get_db
from ..databases import schemas

router = APIRouter()


class DetectionClass(str, Enum):

    all_classes = "all"
    truck = "truck"
    person = "person"
    car = "car"
    motorbike = "motorbike"
    bus = "bus"


@router.get("/recent", response_model=List[schemas.JamCamVideo])
async def cam_recent(
    camera_id: str,
    detection_class: DetectionClass = DetectionClass.all_classes,
    starttime: datetime = None,
    endtime: datetime = None,
    db: Session = Depends(get_db),
):

    print(
        schemas.get_jamcam_recent(
            db, camera_id, detection_class, starttime, endtime, output_type="sql"
        )
    )

    return schemas.get_jamcam_recent(
        db, camera_id, detection_class, starttime, endtime
    ).all()


@router.get("/snapshot")
async def cam_snapshot(id: str):
    return
