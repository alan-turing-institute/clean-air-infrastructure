from typing import List
from pydantic import BaseModel
from datetime import datetime


class JamCamVideo(BaseModel):

    counts: int
    detection_class: str
    creation_datetime: datetime = None

    class Config:
        orm_mode = True
