"""Return Schemas for Historic Forecast routes"""
# pylint: disable=C0115
from typing import List, Tuple
from datetime import datetime
from pydantic import BaseModel
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

    NO2_var: str
    NO2_mean: str
    measurement_start_utc: datetime
    
@dataclass
class ForecastGeojson:

    id: str
    type: str
    geometry: str
    properties: ForecastProperties
       
@dataclass
class ForecastGeojsonCollection(BaseModel):
    ForecastGeojson

