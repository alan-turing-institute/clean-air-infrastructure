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


@dataclass
class Properties:
    camera_id: str


@dataclass
class Geometry:
    type: str
    coordinates: List[Union[Tuple[float, float], Tuple[float, float, float]]]


@dataclass
class Feature:
    type: str
    geometry: Geometry
    properties: Properties


@dataclass
class FeatureCollectionPy:
    type: str
    features: List[Feature]


# # print(Geometry(type="Polygon", coordinates=[[0, 0], [10, 10], [10, 0, 0.5]]))
# geom = Geometry(type="Polygon", coordinates=[[0, 0], [10, 10], [10, 0, 0.5]])
# prop = Properties(camera_id="swsdf")

# print(geom)
# print(prop)
# print(Feature(type="Feature", geometry=geom, properties=prop))

# print(Properties(camera_id="swsdf"))
