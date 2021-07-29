"""Return Schemas for JamCam routes"""
# pylint: disable=C0115
from typing import List, Tuple
from datetime import datetime, timezone, date
from pydantic import BaseModel, validator
from pydantic.dataclasses import dataclass
from sqlalchemy import text


TWELVE_HOUR_INTERVAL = text("interval '12 hour'")

# pylint: disable=E0213, R0201
class UTCTime(BaseModel):

    measurement_start_utc: datetime

    @validator("measurement_start_utc")
    def contains_timezone(cls, v: datetime) -> datetime:
        """Enforce presence of timezone in datetime objects"""
        if v.tzinfo:
            return v
        return v.replace(tzinfo=timezone.utc)


class JamCamAvailable(UTCTime):
    class Config:
        orm_mode = True


class JamCamBase(BaseModel):

    camera_id: str

    class Config:
        orm_mode = True


class JamCamCounts(JamCamBase):

    counts: int

    class Config:
        orm_mode = True


class JamCamAverageCounts(JamCamBase):

    counts: float

    class Config:
        orm_mode = True


class JamCamVideo(JamCamCounts, UTCTime):

    detection_class: str


class JamCamVideoAverage(JamCamAverageCounts, UTCTime):

    detection_class: str
    measurement_start_utc: datetime


class JamCamDailyAverage(JamCamAverageCounts):

    camera_id: str
    detection_class: str
    counts: int


class JamCamStabilitySummaryData(JamCamBase):

    score: int


class JamCamStabilityRawData(JamCamBase):

    mse_diff_n1: float
    mse_diff_0: float
    mse_diff_avg0: float
    ssim_diff_n1: float
    ssim_diff_0: float
    ssim_diff_avg0: float
    date: date
    is_cp: bool

class JamCamConfidentDetections(JamCamBase):

    date: date
    detection_class: str
    count: int


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


class JamCamMetaData(BaseModel):
    id: str
    lat: float
    lon: float
    flag: int

    class Config:
        orm_mode = True
