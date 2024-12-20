"""JamCam API routes"""

import datetime

# pylint: disable=C0116
from typing import List, Dict, Tuple, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from sqlalchemy.orm import Session
from urbanair.databases.queries import get_jamcam_metadata
from urbanair.queries.jamcam import get_tomtom_data

from ...databases import get_db, all_or_404
from ...databases.queries import (
    get_jamcam_available,
    get_jamcam_raw,
    get_jamcam_hourly,
    get_jamcam_daily,
    get_jamcam_today,
    get_jamcam_stability_summary,
    get_jamcam_stability_raw,
    get_jamcam_confident_detections,
)
from ...databases.schemas.jamcam import (
    JamCamVideo,
    JamCamVideoAverage,
    JamCamAvailable,
    JamCamMetaData,
    JamCamDailyAverage,
    JamCamStabilitySummaryData,
    JamCamStabilityRawData,
    JamCamConfidentDetections,
)
from ...types import DetectionClass

router = APIRouter()

ONE_WEEK_SECONDS = 7 * 24 * 60 * 60
ONE_DAYS_SECONDS = 1 * 24 * 60 * 60


def common_jamcam_params(
    camera_id: str = Query(None, description="A unique JamCam id"),
    detection_class: DetectionClass = Query(
        DetectionClass.all_classes, description="Class of object"
    ),
    starttime: datetime.datetime = Query(
        None,
        description="""ISO UTC datetime to request data from""",
    ),
    endtime: datetime.datetime = Query(
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
                detail="""Cannot request more than one week of data in a single call when camera_id is provided. Check startime and endtime parameters""",  # noqa
            )

        if not camera_id and (seconds_requested > ONE_DAYS_SECONDS):
            raise HTTPException(
                422,
                detail="""Cannot request more than two days of data in a single call when no camera_id is provided. Check startime and endtime parameters""",  # noqa
            )

    return {
        "camera_id": camera_id,
        "detection_class": detection_class,
        "starttime": starttime,
        "endtime": endtime,
    }


@router.get(
    "/available",
    description="""Check what jamcam data is available by hour.
    If no camera_id is provided returns an entry if data is available at any camera.
    If starttime and endtime are not provided checks all availability""",
    response_model=List[JamCamAvailable],
)
def camera_available(
    commons: dict = Depends(common_jamcam_params),
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:

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
    commons: dict = Depends(common_jamcam_params),
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:

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
    description="Request counts of objects at jamcam cameras averaged by hour.",
)
def camera_hourly_average(
    commons: dict = Depends(common_jamcam_params),
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:

    data = get_jamcam_hourly(
        db,
        commons["camera_id"],
        commons["detection_class"],
        commons["starttime"],
        commons["endtime"],
    )

    return all_or_404(data)


def jamcam_daily_params(
    camera_id: Optional[str] = Query(None, description="(optional) A unique JamCam id"),
    detection_class: DetectionClass = Query(
        DetectionClass.all_classes, description="Class of object"
    ),
    date: Optional[datetime.date] = Query(
        None,
        description="(optional) ISO UTC date for which to request data.",
    ),
) -> Dict:
    """Common parameters in jamcam routes.
    If a camera_id is provided request up to 1 week of data
    If no camera_id is provided request up to 24 hours of data
    """
    # pylint: disable=C0301

    if date == datetime.date.today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Data is only available for historical dates at this endpoint.\
                 For today, use the /today endpoint.",
        )

    return {
        "camera_id": camera_id,
        "detection_class": detection_class,
        "date": date,
    }


@router.get(
    "/daily",
    response_model=List[JamCamDailyAverage],
    description="Request averaged counts of objects at jamcam cameras day",
)
def camera_daily_average(
    commons: dict = Depends(jamcam_daily_params),
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:

    data = get_jamcam_daily(
        db,
        commons["camera_id"],
        commons["detection_class"],
        commons["date"],
    )

    return all_or_404(data)


def jamcam_today_params(
    camera_id: Optional[str] = Query(None, description="(optional) A unique JamCam id"),
    detection_class: DetectionClass = Query(
        DetectionClass.all_classes, description="Class of object"
    ),
) -> Dict:
    """Common parameters in jamcam routes.
    If a camera_id is provided request up to 1 week of data
    If no camera_id is provided request up to 24 hours of data
    """

    return {
        "camera_id": camera_id,
        "detection_class": detection_class,
    }


@router.get(
    "/today",
    response_model=List[JamCamDailyAverage],
    description="Request averaged counts of objects at jamcam cameras for today.",
)
def camera_today_average(
    commons: dict = Depends(jamcam_today_params),
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:

    data = get_jamcam_today(db, commons["camera_id"], commons["detection_class"])

    return all_or_404(data)


@router.get(
    "/metadata",
    response_model=List[JamCamMetaData],
    description="The locations and other metadata of all jamcams.",
)
def metadata(
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:

    data = get_jamcam_metadata(db)

    return all_or_404(data)


def jamcam_stability_score_params(
    camera_id: Optional[str] = Query(None, description="(optional) A unique JamCam id"),
) -> Dict:
    """Common parameters in jamcam routes.
    If a camera_id is provided request only that score, otherwise return all
    """

    return {
        "camera_id": camera_id,
    }


@router.get(
    "/stability_score",
    response_model=List[JamCamStabilitySummaryData],
    description="The stability score calculated per camera, integer valued where \
                lower is better. Constructed from change point and outlier detection over \
                `ssim_diff_avg0`.",
)
def stability_score(
    commons: dict = Depends(jamcam_stability_score_params),
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:

    data = get_jamcam_stability_summary(db, commons["camera_id"])

    return all_or_404(data)


def jamcam_stability_raw_params(
    camera_id: Optional[str] = Query(None, description="(optional) A unique JamCam id"),
) -> Dict:
    """Common parameters in jamcam routes.
    If a camera_id is provided request only that score, otherwise return all
    """

    return {
        "camera_id": camera_id,
    }


@router.get(
    "/stability_raw",
    response_model=List[JamCamStabilityRawData],
    description="The stability raw data calculated per camera. `mse_diff_avg0` and \
        `ssim_diff_avg0` are of most value, describing the Mean Squared Error and \
        Structural Similarity Index Measure per camera each day against a reference \
        avg0` set constructed from initial data collection samples. A \
        comparison against the first ever frame (`_0') and a frame \
        sampled from the day before (`_n1`) are also available \
        however noisy.",
)
def stability_raw(
    commons: dict = Depends(jamcam_stability_raw_params),
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:

    data = get_jamcam_stability_raw(db, commons["camera_id"])

    return all_or_404(data)


@router.get(
    "/traffic_data", description="Third party traffic data", include_in_schema=False
)
def traffic_data() -> Optional[dict]:
    return {"success": True}


@router.get(
    "/traffic_data/{zoom}/{x}/{y}",
    description="Third party traffic data.",
    include_in_schema=False,
)
def traffic_data_tiles(zoom: int, x: int, y: int) -> Optional[Response]:

    res = get_tomtom_data(zoom, x, y)
    if res.ok:
        return Response(
            content=res.content, status_code=res.status_code, media_type="bytes"
        )

    if res.status_code == 403:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Invalid TomTom API key",
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error with request to TomTom API",
    )


@router.get(
    "/confidence",
    response_model=List[JamCamConfidentDetections],
    description="Request counts of objects at jamcam cameras with above 0.8 \
        detection confidence from the object detection model.",
)
def confident_detections(
    commons: dict = Depends(common_jamcam_params),
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:

    data = get_jamcam_confident_detections(
        db,
        commons["camera_id"],
        commons["detection_class"],
        commons["starttime"],
        commons["endtime"],
    )

    return all_or_404(data)
