"""Fake data generators which can be inserted into database"""

import random
from typing import Optional, Union, Tuple
import string
import re
import uuid
from datetime import datetime, date, timedelta
from pydantic import BaseModel, validator
from scipy.stats import uniform, norm
import numpy as np
from ....types import Source, FeatureNames
from ....databases.tables import SatelliteBox

# pylint: disable=E0213,R0201

# Point regular expression
RE_POINT = re.compile("^SRID=4326;POINT\((\d*\.?\d*) (\d*\.?\d*)\)$")


def get_random_string(length: int) -> str:
    "Random string of length"
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


def gen_point_id(v: Optional[uuid.UUID]) -> uuid.UUID:
    "Random uuid"
    if v:
        return v
    return uuid.uuid4()


def gen_site_code(v: Optional[str]) -> str:
    "Random site code"
    if v:
        return v
    return get_random_string(4)


def gen_norm_value(v: Optional[float]) -> float:
    "random exp normal"
    if v:
        return v
    return np.exp(norm.rvs(0, 1))


class MetaPointSchema(BaseModel):
    "Meta Point Schema"
    id: Optional[uuid.UUID]
    source: str
    location: Optional[str]

    _gen_point_id = validator("id", allow_reuse=True, always=True)(gen_point_id)

    @validator("location", always=True)
    def gen_location(cls, v):
        "Random location. These will always be within the border of HexGrid"
        if v:
            return v
        min_lon = -0.33
        max_lon = 0.11
        min_lat = 51.4
        max_lat = 51.6

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
        "Generate end time one hour after start time"
        if v:
            return v
        return values["measurement_start_utc"] + timedelta(hours=1)


class AQESiteSchema(LAQNSiteSchema):
    "AQE Site schema"
    site_name: Optional[str]

    _gen_site_name = validator("site_name", allow_reuse=True, always=True)(
        gen_site_code
    )


class AQEReadingSchema(LAQNReadingSchema):
    "AQE Reading schema"


class SatelliteBoxSchema(BaseModel):
    "Satellite Box Schema"

    centroid: Union[str, Tuple[float, float]]
    geom: Optional[str]
    id: Optional[uuid.UUID]

    _gen_point_id = validator("id", allow_reuse=True, always=True)(gen_point_id)

    @validator("centroid", always=True)
    def validate_point(cls, v):
        """Generate end time one hour after start time
        
        Example:
            'SRID=4326;POINT(4.2234 2232342.2342)'
        """

        if isinstance(v, str):

            if RE_POINT.match(v):
                return v
            raise ValueError("Not a valid Point string")

        if isinstance(v, tuple):
            if len(v) != 2:
                raise ValueError("v must be tuple of length 2")
            return f"SRID=4326;POINT({v[0]} {v[1]})"

    @validator("geom", always=True)
    def gen_geom(cls, v, values):
        "Generate end time one hour after start time"
        if v:
            raise ValueError("Do not provide a value. Calculated automatically")

        centroid = values["centroid"]
        centroid_points = centroid[16:].strip(")").split(" ")

        return SatelliteBox.build_box_ewkt(
            float(centroid_points[1]), float(centroid_points[0]), 0.05
        )

    @property
    def centroid_tuple(self):

        return [float(i) for i in self.centroid[16:].strip(")").split(" ")]


class SatelliteGridSchema(BaseModel):
    "Satellite Grid Schema"

    point_id: uuid.UUID
    box_id: uuid.UUID


class StaticFeaturesSchema(BaseModel):
    "Static features schema"
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
