"""Fake data generators which can be inserted into database"""

from typing import Iterable, Optional
from pydantic import BaseModel, validator
from pydantic.dataclasses import dataclass
import random
from scipy.stats import uniform
import string
import uuid
from datetime import datetime, date
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

