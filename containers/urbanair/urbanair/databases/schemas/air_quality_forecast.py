"""Return schemas for air quality forecast routes"""
from typing import List, Tuple
from datetime import datetime
import json
from pydantic import BaseModel
from pydantic.validators import str_validator
from pydantic.dataclasses import dataclass
from pydantic.types import UUID


class ForecastResultBase(BaseModel):
    point_id: str
    measurement_start_utc: datetime
    NO2_mean: float
    NO2_var: float

    class Config:
        orm_mode = True
