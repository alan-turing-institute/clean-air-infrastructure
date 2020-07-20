"""Return Schemas for Historic Forecast routes"""
# pylint: disable=C0115
from typing import List, Tuple
from datetime import datetime
import json
from pydantic import BaseModel
from pydantic.validators import str_validator
from pydantic.dataclasses import dataclass


class ForecastBase(BaseModel):

    instance_id: str
    fit_start_time: datetime
    tag: str
    model_name: str

    class Config:
        orm_mode = True


class ForecastResultBase(BaseModel):

    instance_id: str
    data_id: str
    point_id: str
    measurement_start_utc: datetime
    NO2_mean: str

    class Config:
        orm_mode = True


# GeoJson Types


@dataclass
class ForecastProperties:
    # pylint: disable-msg=C0103
    measurement_start_utc: datetime
    NO2_mean: str
    NO2_var: str


class ForecastGeometry(BaseModel):

    type: str
    coordinates: List[Tuple[float, float]]

    @classmethod
    def __get_validators__(cls):
        yield str_validator
        yield cls.validate

    # pylint: disable-msg=W0221
    @classmethod
    def validate(cls, v: str):
        res = json.loads(v)
        return {"type": res.get("type"), "coordinates": res.get("coordinates")}


class AirPolutionFeature(BaseModel):

    id: str
    geometry: ForecastGeometry
    properties: ForecastProperties

    class Config:
        orm_mode = True


class AirPolutionFeatureCollection(BaseModel):

    out: List[AirPolutionFeature]
