"""JamCam API routes"""
# pylint: disable=C0116
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from ..databases import get_db, all_or_404
from ..databases.schemas.jamcam import (
    JamCamVideo,
    JamCamCounts,
    JamCamFeatureCollection,
    JamCamAvailable,
)
from ..databases.queries import (
    get_jamcam_available,
    get_jamcam_recent,
    get_jamcam_info,
    get_jamcam_snapshot,
)
from ..types import DetectionClass

router = APIRouter()


@router.get(
    "/camera_info",
    description="GeoJSON: JamCam camera locations.",
    response_model=JamCamFeatureCollection,
)
async def camera_info() -> Response:
    "Get camera info"
    return get_jamcam_info()


@router.get(
    "/available",
    description="""Check what jamcam data is available by hour.
    If no camera_id is provided returns entry if data is available at any camera.
    If starttime and endtime are not provided checks all availability""",
    response_model=List[JamCamAvailable],
)
async def camera_available(
    camera_id: str = Query(None, description="A unique JamCam id"),
    detection_class: DetectionClass = Query(
        DetectionClass.all_classes, description="Class of object"
    ),
    starttime: datetime = Query(
        None, description="""ISO UTC datetime to request data from""",
    ),
    endtime: datetime = Query(
        None,
        description="ISO UTC datetime to request data up to (not including this datetime)",
    ),
    db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_jamcam_available(db, camera_id, detection_class, starttime, endtime)

    return all_or_404(data)


@router.get(
    "/raw",
    description="""Request counts of objects at jamcam cameras. 
    If no camera_id is provided returns data for all cameras (slow).
    If not starttime and endtime are provided returns the last 12 hours of available data.
""",
    response_model=List[JamCamVideo],
)
async def camera_raw(
    camera_id: str = Query(None, description="A unique JamCam id"),
    detection_class: DetectionClass = Query(
        DetectionClass.all_classes, description="Class of object"
    ),
    starttime: datetime = Query(
        None, description="""ISO UTC datetime to request data from""",
    ),
    endtime: datetime = Query(
        None,
        description="ISO UTC datetime to request data up to (not including this datetime)",
    ),
    db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_jamcam_recent(db, camera_id, detection_class, starttime, endtime)

    return all_or_404(data)


@router.get(
    "/hourly",
    response_model=List[JamCamVideo],
    description="""Request counts of objects at jamcam cameras aggregated by hour.
""",
)
async def camera_hourly(
    camera_id: str = Query(None, description="A unique JamCam id"),
    detection_class: DetectionClass = Query(
        DetectionClass.all_classes, description="Class of object"
    ),
    starttime: datetime = Query(
        None,
        description="""ISO UTC datetime to request data from.
        If no starttime or endtime provided will return the last 12 hours of availble data""",
    ),
    endtime: datetime = Query(
        None,
        description="ISO UTC datetime to request data up to (not including this datetime)",
    ),
    db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_jamcam_snapshot(db, camera_id, detection_class, starttime, endtime)

    return all_or_404(data)
