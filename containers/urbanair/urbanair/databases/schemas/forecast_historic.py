"""Return Schemas for Historic Forecast routes"""
# pylint: disable=C0115
from typing import List, Tuple
from datetime import datetime
from pydantic import BaseModel,ValidationError, conint
from pydantic.dataclasses import dataclass
from pydantic.validators import int_validator
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


@dataclass
class ForecastGeometry:
    type: str
    coordinates:List[Tuple[float, float]]

@dataclass
class ForecastGeojson:
    point_id: str
    geometry: ForecastGeometry
    properties: ForecastProperties
      
@dataclass
class AirPolutionFeatureCollection(BaseModel):
    features: List[ForecastGeojson]

