"""Fake data generators which can be inserted into database"""

from typing import Iterable, Optional
from pydantic import BaseModel, validator, Json
from pydantic.dataclasses import dataclass
import random
from scipy.stats import uniform, norm
import numpy as np
import string
import uuid
from datetime import datetime, date, timedelta
from ....utils.hashing import hash_fn
from ....types import Source


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


def gen_point_id(v) -> uuid.UUID:
    if v:
        return v
    return uuid.uuid4()


def gen_site_code(v) -> str:
    if v:
        return v
    return get_random_string(4)


class MetaPointSchema(BaseModel):

    id: Optional[uuid.UUID]
    source: str
    location: Optional[str]

    _gen_point_id = validator("id", allow_reuse=True, always=True)(gen_point_id)

    @validator("location", always=True)
    def gen_location(cls, v):
        if v:
            return v
        min_lon = -0.508854438
        max_lon = 0.334270337
        min_lat = 51.286678732
        max_lat = 51.692470396

        point = uniform.rvs([min_lon, min_lat], [max_lon - min_lon, max_lat - min_lat])
        return f"SRID=4326;POINT({point[0]} {point[1]})"


class LAQNSiteSchema(BaseModel):

    site_code: Optional[str]
    point_id: uuid.UUID
    site_type: str = "Roadside"
    date_opened: date
    date_closed: Optional[datetime]

    _gen_site_code = validator("site_code", allow_reuse=True, always=True)(
        gen_site_code
    )


class LAQNReadingSchema(BaseModel):

    site_code: str
    species_code: str
    measurement_start_utc: datetime
    measurement_end_utc: Optional[datetime]
    value: Optional[float]

    @validator("value", always=True)
    def gen_value(cls, v):
        if v:
            return v
        return np.exp(norm.rvs(0, 1))

    @validator("measurement_end_utc", always=True)
    def gen_measurement_end_time(cls, v, values):
        if v:
            return v
        else:
            return values["measurement_start_utc"] + timedelta(hours=1)


class AirQualityModelShema(BaseModel):
    model_name: str = "svgp"
    param_id: Optional[str]
    model_param: Optional[Json]

    @validator("param_id", always=True)
    def gen_param_id(cls, v):
        if v:
            return v
        return hash_fn(str(random.random()))

    @validator("model_param", always=True)
    def gen_model_param(cls, v):
        if v:
            return v
        return '{"params": "empty"}'
   

class AirQualityDataShema(BaseModel):
    data_id: Optional[str]
    data_config: Optional[Json]
    preprocessing: Optional[Json]

    @validator("data_id", always=True)
    def gen_data_id(cls, v):
        if v:
            return v
        return hash_fn(str(random.random()))

    
    @validator("data_config", always=True)
    def gen_data_config(cls, v):
        if v:
            return v
        return '{"data_config": "empty"}'

    
    @validator("preprocessing", always=True)
    def gen_preprocessing(cls, v):
        if v:
            return v
        return '{"preprocessing": "empty"}'
