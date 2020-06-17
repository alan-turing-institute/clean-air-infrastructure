from fastapi import APIRouter, Depends, Query, Response
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..databases import get_db, all_or_404
from ..databases.schemas.jamcam import (
    JamCamVideo,
    JamCamCounts,
    JamCamLoc,
    JamCamFeatureCollection,
)
from ..databases.queries.jamcam import (
    get_jamcam_recent,
    get_jamcam_info,
    get_jamcam_snapshot,
)
from ..types import DetectionClass

router = APIRouter()


@router.get(
    "/camera_info",
    description="GeoJSON: JamCam camera locations",
    response_model=JamCamFeatureCollection,
)
async def camera_info() -> Response:

    return get_jamcam_info()


@router.get(
    "/recent",
    description="""Request counts of objects at jamcam cameras
""",
    response_model=List[JamCamVideo],
)
async def cam_recent(
    camera_id: str = Query(None, description="A unique JamCam id"),
    detection_class: DetectionClass = Query(
        DetectionClass.all_classes, description="Class of object"
    ),
    starttime: datetime = Query(
        None,
        description="ISO UTC datetime to request data from. If no starttime or endtime provided will return the last 12 hours of availble data",
    ),
    endtime: datetime = Query(
        None,
        description="ISO UTC datetime to request data up to (not including this datetime)",
    ),
    db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_jamcam_recent(db, camera_id, detection_class, starttime, endtime)

    return all_or_404(data)


@router.get("/snapshot", response_model=List[JamCamCounts])
async def cam_snapshot(
    detection_class: DetectionClass = DetectionClass.all_classes,
    db: Session = Depends(get_db),
) -> List[Dict]:

    return get_jamcam_snapshot(db, detection_class)
