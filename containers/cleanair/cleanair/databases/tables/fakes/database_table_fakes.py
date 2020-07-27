"""Fake data generators which can be inserted into database"""

from typing import Iterable, Optional
from pydantic import BaseModel, validator
from pydantic.dataclasses import dataclass
import random
from scipy.stats import uniform, norm
import numpy as np
import string
import uuid
from datetime import datetime, date, timedelta
from ....types import Source, FeatureNames


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


def gen_norm_value(v) -> float:
    if v:
        return v
    else:
        return np.exp(norm.rvs(0, 1))


class MetaPointSchema(BaseModel):
    "Meta Point Schema"
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
    "LAQN Site Schema"
    site_code: Optional[str]
    point_id: uuid.UUID
    site_type: str = "Roadside"
    date_opened: date
    date_closed: Optional[datetime]

    _gen_site_code = validator("site_code", allow_reuse=True, always=True)(
        gen_site_code
    )


class LAQNReadingSchema(BaseModel):
    "LAQN Reading Schema"
    site_code: str
    species_code: str
    measurement_start_utc: datetime
    measurement_end_utc: Optional[datetime]
    value: Optional[float]

    _gen_value = validator("value", always=True, allow_reuse=True)(gen_norm_value)

    @validator("measurement_end_utc", always=True)
    def gen_measurement_end_time(cls, v, values):
        if v:
            return v
        else:
            return values["measurement_start_utc"] + timedelta(hours=1)


class AQESiteSchema(LAQNSiteSchema):
    "AQE Site schema"
    site_name: Optional[str]

    _gen_site_name = validator("site_name", allow_reuse=True, always=True)(
        gen_site_code
    )


class AQEReadingSchema(LAQNReadingSchema):
    "AQE Reading schema"


class StaticFeaturesSchema(BaseModel):

    point_id: uuid.UUID
    feature_name: FeatureNames
    feature_source: Source
    value_1000: Optional[float]
    value_500: Optional[float]
    value_200: Optional[float]
    value_100: Optional[float]
    value_10: Optional[float]

    _gen_value_1000 = validator("value_1000", always=True, allow_reuse=True)(
        gen_norm_value
    )
    _gen_value_500 = validator("value_500", always=True, allow_reuse=True)(
        gen_norm_value
    )
    _gen_value_200 = validator("value_200", always=True, allow_reuse=True)(
        gen_norm_value
    )
    _gen_value_100 = validator("value_100", always=True, allow_reuse=True)(
        gen_norm_value
    )
    _gen_value_10 = validator("value_10", always=True, allow_reuse=True)(gen_norm_value)
