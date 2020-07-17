"""Return Schemas for Historic Forecast routes"""
# pylint: disable=C0115
from typing import List, Tuple, Optional
from datetime import datetime
import json, re
from pydantic import BaseModel, ValidationError, conint, validator
from pydantic.dataclasses import dataclass
from sqlalchemy import text


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

    measurement_start_utc: datetime
    NO2_mean: str
    NO2_var: str

class ForecastGeometry(str):

    type: str = None
    coordinates: List[Tuple[float, float]] = [[]]


    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(
            type = None,
            coordinates= [[]]
        )
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError('string required')
        return json.loads(v)

    def __repr__(self):
        return f'ForecastGeometry({super().__repr__()})'
 
    
 
class AirPolutionFeature(BaseModel):

    id: str
    geometry: ForecastGeometry
    properties: ForecastProperties

    class Config:
        orm_mode = True

    # @validator("geometry")
    # def geom_valid(cls, v):
    #     return json.loads(v)


class AirPolutionFeatureCollection(BaseModel):

    out: List[AirPolutionFeature]
