from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import func, text
from datetime import datetime
from cleanair.databases.tables import JamCamVideoStats
from cleanair.decorators import db_query


TWELVE_HOUR_INTERVAL = text("interval '12 hour'")


class JamCamBase(BaseModel):

    camera_id: str
    counts: int

    class Config:
        orm_mode = True


class JamCamVideo(JamCamBase):

    camera_id: str
    counts: int
    detection_class: str
    measurement_start_utc: datetime
