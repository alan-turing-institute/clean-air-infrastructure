"""JamCam API routes"""
# pylint: disable=C0116
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response, HTTPException
from sqlalchemy.orm import Session
from ..databases import get_db, all_or_404
from ..databases.schemas.jamcam import (
    JamCamVideo,
    JamCamVideoAverage,
    JamCamFeatureCollection,
    JamCamAvailable,
)
from ..databases.queries import (
    get_jamcam_available,
    get_jamcam_raw,
    get_jamcam_info,
    get_jamcam_hourly,
)
from ..types import DetectionClass

router = APIRouter()

ONE_WEEK_SECONDS = 7 * 24 * 60 * 60
ONE_DAYS_SECONDS = 1 * 24 * 60 * 60


async def common_jamcam_params(
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
) -> Dict:
    """Common parameters in jamcam routes.
       If a camera_id is provided request up to 1 week of data
       If no camera_id is provided request up to 24 hours of data
    """
    # pylint: disable=C0301
    if starttime and endtime:
        seconds_requested = (endtime - starttime).total_seconds()

        if camera_id and (seconds_requested > ONE_WEEK_SECONDS):
            raise HTTPException(
                422,
                detail="""Cannot request more than one week of data in a single call when camera_id is provided. Check startime and endtime parameters""",
            )

        if not camera_id and (seconds_requested > ONE_DAYS_SECONDS):
            raise HTTPException(
                422,
                detail="""Cannot request more than two days of data in a single call when no camera_id is provided. Check startime and endtime parameters""",
            )

    return {
        "camera_id": camera_id,
        "detection_class": detection_class,
        "starttime": starttime,
        "endtime": endtime,
    }


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
    If no camera_id is provided returns an entry if data is available at any camera.
    If starttime and endtime are not provided checks all availability""",
    response_model=List[JamCamAvailable],
)
async def camera_available(
    commons: dict = Depends(common_jamcam_params), db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_jamcam_available(
        db,
        commons["camera_id"],
        commons["detection_class"],
        commons["starttime"],
        commons["endtime"],
    )

    return all_or_404(data)


@router.get(
    "/raw",
    description="Request counts of objects at jamcam cameras.",
    response_model=List[JamCamVideo],
)
async def camera_raw_counts(
    commons: dict = Depends(common_jamcam_params), db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_jamcam_raw(
        db,
        commons["camera_id"],
        commons["detection_class"],
        commons["starttime"],
        commons["endtime"],
    )

    return all_or_404(data)


@router.get(
    "/hourly",
    response_model=List[JamCamVideoAverage],
    description="Request counts of objects at jamcam cameras averaged by hour",
)
async def camera_hourly_average(
    commons: dict = Depends(common_jamcam_params), db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_jamcam_hourly(
        db,
        commons["camera_id"],
        commons["detection_class"],
        commons["starttime"],
        commons["endtime"],
    )

    return all_or_404(data)
