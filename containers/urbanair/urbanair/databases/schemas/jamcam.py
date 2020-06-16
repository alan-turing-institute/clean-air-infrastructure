from typing import List, Optional, Tuple, Union, Dict
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from sqlalchemy import func, text
from datetime import datetime
from cleanair.databases.tables import JamCamVideoStats
from cleanair.decorators import db_query


TWELVE_HOUR_INTERVAL = text("interval '12 hour'")


class JamCamBase(BaseModel):

    camera_id: str

    class Config:
        orm_mode = True


class JamCamCounts(JamCamBase):

    counts: int

    class Config:
        orm_mode = True


class JamCamLoc(JamCamBase):

    lon: float
    lat: float

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
