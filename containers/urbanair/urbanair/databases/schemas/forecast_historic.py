"""Return Schemas for Historic Forecast routes"""
# pylint: disable=C0115
from typing import List, Tuple, Optional
from datetime import datetime
import json
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

class ForecastGeometry(BaseModel):
    type: str = None
    coordinates: List[Tuple[float, float]] = []

    class Config:
        arbitrary_types_allowed= True
        orm_mode = True
  
    
    # @validator('type', 'coordinates')
    # def json_decode(cls, v):
    #     try:
    #         return json.loads(v)
    #     except ValueError:
    #         pass
       
    
 
class AirPolutionFeature(BaseModel):

    id: str
    geometry: ForecastGeometry
    properties: ForecastProperties

    class Config:
        arbitrary_types_allowed= True
        orm_mode = True

    @validator("geometry")
    def geom_valid(cls, v):
        return json.loads(v)

       


class AirPolutionFeatureCollection(BaseModel):

    out: List[AirPolutionFeature]
