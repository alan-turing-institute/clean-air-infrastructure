"""Return Schemas for Historic Forecast routes"""
# pylint: disable=C0115
from typing import List, Tuple
from datetime import datetime
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from sqlalchemy import text


class ForecastAvailable(BaseModel):

    instance_id: str
    fit_start_time: datetime
    tag: str
    model_name: str

    class Config:
        orm_mode = True


# GeoJson Types


@dataclass
class ForecastProperties:
    instance_id: str
