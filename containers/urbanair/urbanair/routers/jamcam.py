from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from geojson import Feature, Point, FeatureCollection
import requests
from ..databases import get_db
from ..databases.schemas.jamcam import JamCamVideo, JamCamCounts, JamCamLoc
from ..databases.queries.jamcam import get_jamcam_recent
from ..types import DetectionClass

router = APIRouter()


@router.get(
    "/camera_info", description="List of jamcam cameras and their location",
)
async def camera_info():

    cam_req = requests.get("https://api.tfl.gov.uk/Place/Type/JamCam/")
    if cam_req.status_code != 200:
        raise HTTPException(
            status_code=404,
            detail="Could not get jamcam info. Please contact API administrator",
        )

    cam_data = cam_req.json()

    output = list(
        map(
            lambda x: {
                "camera_id": x["id"].split("_")[1],
                "lat": x["lat"],
                "lon": x["lon"],
            },
            cam_data,
        )
    )

    out = FeatureCollection(
        [
            Feature(
                geometry=Point((x["lat"], x["lon"])),
                properties={"camera_id": x["camera_id"]},
            )
            for x in output
        ]
    )

    print(out)

    return out


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
):
    return get_jamcam_recent(db, camera_id, detection_class, starttime, endtime).all()


@router.get("/snapshot", response_model=List[JamCamCounts])
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
