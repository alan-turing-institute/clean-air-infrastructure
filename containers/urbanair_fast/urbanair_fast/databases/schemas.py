from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import func, text
from datetime import datetime
from cleanair.databases.tables import JamCamVideoStats
from cleanair.decorators import db_query


TWELVE_HOUR_INTERVAL = text("interval '12 hour'")


class JamCamVideo(BaseModel):

    counts: int
    detection_class: str
    creation_datetime: datetime = None

    class Config:
        orm_mode = True


@db_query
def get_jamcam_recent(
    db,
    camera_id: str,
    detection_class="all",
    starttime: Optional[datetime] = None,
    endtime: Optional[datetime] = None,
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
    ).filter(JamCamVideoStats.camera_id == camera_id + ".mp4")

    # Filter by time
    if endtime:
        res = res.filter(JamCamVideoStats.creation_datetime < endtime.isoformat())
    if starttime:
        res = res.filter(JamCamVideoStats.creation_datetime >= starttime.isoformat())
    else:
        res = res.filter(
            JamCamVideoStats.video_upload_datetime
            > max_video_upload_datetime.c.max_video_upload_datetime
            - TWELVE_HOUR_INTERVAL
        )

    # Filter by detection class
    if detection_class != "all":
        res = res.filter(JamCamVideoStats.detection_class == detection_class)

    return res.order_by(JamCamVideoStats.creation_datetime)
