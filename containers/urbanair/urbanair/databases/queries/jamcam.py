from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import func, text
from datetime import datetime
from cleanair.databases.tables import JamCamVideoStats
from cleanair.decorators import db_query
from ...types import DetectionClass

TWELVE_HOUR_INTERVAL = text("interval '12 hour'")


@db_query
def get_jamcam_recent(
    db,
    camera_id: Optional[str],
    detection_class: DetectionClass = DetectionClass.all_classes,
    starttime: Optional[datetime] = None,
    endtime: Optional[datetime] = None,
):

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
