"""Return Schemas for JamCam routes"""
# pylint: disable=C0115
from typing import List, Tuple
from datetime import datetime
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from sqlalchemy import text


TWELVE_HOUR_INTERVAL = text("interval '12 hour'")


class JamCamBase(BaseModel):

    camera_id: str

    class Config:
        orm_mode = True


class JamCamCounts(JamCamBase):

    counts: int

    class Config:
        orm_mode = True


class JamCamVideo(JamCamCounts):

    detection_class: str
    measurement_start_utc: datetime


# GeoJson Types


@dataclass
class JamCamProperties:
    camera_id: str


@dataclass
class JamCamGeometry:
    type: str
    coordinates: Tuple[float, float]


@dataclass
class JamCamFeature:
    type: str
    id: str
    geometry: JamCamGeometry
    properties: JamCamProperties


@dataclass
class JamCamFeatureCollection(BaseModel):
    type: str
    features: List[JamCamFeature]
