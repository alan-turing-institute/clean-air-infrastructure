"""JamCam API routes"""
# pylint: disable=C0116
from typing import List, Dict, Optional
from datetime import datetime, date
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
    get_jamcam_daily,
)
from ..types import DetectionClass

router = APIRouter()

TWO_WEEK_SECONDS = 48 * 24 * 60 * 60
TWO_DAYS_SECONDS = 2 * 24 * 60 * 60
THIRTYONE_DAY_SECONDS = 31 * 24 * 60 * 60
FOUR_DAYS_SECONDS = 4 * 24 * 60 * 60


def common_datetime_jamcam_params(
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

        if camera_id and (seconds_requested > TWO_WEEK_SECONDS):
            raise HTTPException(
                422,
                detail="""Cannot request more than two weeks of data in a single call when camera_id is provided. Check startime and endtime parameters""",
            )

        if not camera_id and (seconds_requested > TWO_DAYS_SECONDS):
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


def common_date_jamcam_params(
    camera_id: str = Query(None, description="A unique JamCam id"),
    detection_class: DetectionClass = Query(
        DetectionClass.all_classes, description="Class of object"
    ),
    startdate: date = Query(None, description="""ISO UTC date to request data from""",),
    enddate: date = Query(
        None,
        description="ISO UTC date to request data up to (not including this datetime)",
    ),
) -> Dict:
    """Common parameters in jamcam routes.
       If a camera_id is provided request up to 1 week of data
       If no camera_id is provided request up to 24 hours of data
    """
    # pylint: disable=C0301
    if startdate and enddate:
        seconds_requested = (enddate - startdate).total_seconds()

        if camera_id and (seconds_requested > THIRTYONE_DAY_SECONDS):
            raise HTTPException(
                422,
                detail="""Cannot request more than 30 days of data in a single call when camera_id is provided. Check startdate and enddate parameters""",
            )

        if not camera_id and (seconds_requested > FOUR_DAYS_SECONDS):
            raise HTTPException(
                422,
                detail="""Cannot request more than four days of data in a single call when no camera_id is provided. Check startdate and enddate parameters""",
            )

    return {
        "camera_id": camera_id,
        "detection_class": detection_class,
        "startdate": startdate,
        "enddate": enddate,
    }


@router.get(
    "/camera_info",
    description="GeoJSON: JamCam camera locations.",
    response_model=JamCamFeatureCollection,
)
def camera_info() -> Response:
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
    commons: dict = Depends(common_datetime_jamcam_params),
    db: Session = Depends(get_db),
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
def camera_raw_counts(
    commons: dict = Depends(common_datetime_jamcam_params),
    db: Session = Depends(get_db),
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
def camera_hourly_average(
    commons: dict = Depends(common_datetime_jamcam_params),
    db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_jamcam_hourly(
        db,
        commons["camera_id"],
        commons["detection_class"],
        commons["starttime"],
        commons["endtime"],
    )

    return all_or_404(data)


@router.get(
    "/daily",
    response_model=List[JamCamVideoAverage],
    description="Request counts of objects at jamcam cameras averaged by day",
)
def camera_daily_average(
    commons: dict = Depends(common_date_jamcam_params), db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_jamcam_daily(
        db,
        commons["camera_id"],
        commons["detection_class"],
        commons["startdate"],
        commons["enddate"],
    )

    return all_or_404(data)

