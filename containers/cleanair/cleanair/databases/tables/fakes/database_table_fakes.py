"""Fake data generators which can be inserted into database"""

import random

from typing import Optional
import string
import uuid
from datetime import datetime, date, timedelta
from pydantic import BaseModel, validator, Json
from scipy.stats import uniform, norm
import numpy as np
from ....utils.hashing import hash_fn
from ....types import Source, FeatureNames

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


def gen_site_code(v) -> str:
    "Random site code"
    if v:
        return v
    return get_random_string(4)


def gen_hash_id(v) -> str:
    "Return a random hash id"
    if v:
        return v
    return hash_fn(str(random.random()))


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
    #pylint: disable=E0213,R0201
    @validator("location", always=True)
    def gen_location(cls, v):
        "Random location"
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
    #pylint: disable=E0213,R0201
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


class AirQualityModelSchema(BaseModel):
    "AirPollution Model Schema"
    model_name: str = "svgp"
    model_param: Optional[Json]
    param_id: Optional[str]

    _gen_hash_id = validator("param_id", allow_reuse=True, always=True)(gen_hash_id)
    #pylint: disable=E0213,R0201
    @validator("model_param", always=True)
    def gen_model_param(cls, v):
        "Generate empty parammeters"
        if v:
            return v
        return '{"params": "empty"}'


class AirQualityDataSchema(BaseModel):
    "AirPollution Data Schema"
    data_id: Optional[str]
    data_config: Optional[Json]
    preprocessing: Optional[Json]

    _gen_hash_id = validator("data_id", allow_reuse=True, always=True)(gen_hash_id)
    #pylint: disable=E0213,R0201
    @validator("data_config", always=True)
    def gen_data_config(cls, v):
        "Generate an empty data config"
        if v:
            return v
        return '{"data_config": "empty"}'

    @validator("preprocessing", always=True)
    def gen_preprocessing(cls, v):
        "Generate an empty preprocessing"
        if v:
            return v
        return '{"preprocessing": "empty"}'


class AirQualityInstanceSchema(BaseModel):
    "AirPollution Instance Schema"
    model_name: str
    param_id: str
    data_id: str
    fit_start_time: datetime
    cluster_id: Optional[str]
    instance_id: Optional[str]
    tag: Optional[str]
    git_hash: Optional[str]

    _gen_hash_instance_id = validator("instance_id", allow_reuse=True, always=True)(
        gen_hash_id
    )
    _gen_hash_cluster_id = validator("cluster_id", allow_reuse=True, always=True)(
        gen_hash_id
    )
    _gen_site_code_git = validator("git_hash", allow_reuse=True, always=True)(
        gen_site_code
    )
    _gen_site_code_tag = validator("tag", allow_reuse=True, always=True)(gen_site_code)


class AirQualityResultSchema(BaseModel):
    "AirPollution Result Schema"
    instance_id: str
    data_id: str
    point_id: uuid.UUID
    measurement_start_utc: datetime
    NO2_mean: Optional[float]
    NO2_var: Optional[float]
    PM10_mean: Optional[float]
    PM10_var: Optional[float]
    PM25_mean: Optional[float]
    PM25_var: Optional[float]
    CO2_mean: Optional[float]
    CO2_var: Optional[float]
    O3_mean: Optional[float]
    O3_var: Optional[float]

    _gen_norm_NO2_mean = validator("NO2_mean", allow_reuse=True, always=True)(
        gen_norm_value
    )
    _gen_norm_NO2_var = validator("NO2_var", allow_reuse=True, always=True)(
        gen_norm_value
    )
    _gen_norm_PM10_mean = validator("PM10_mean", allow_reuse=True, always=True)(
        gen_norm_value
    )
    _gen_norm_PM10_mean = validator("PM10_mean", allow_reuse=True, always=True)(
        gen_norm_value
    )
    _gen_norm_PM25_mean = validator("PM25_mean", allow_reuse=True, always=True)(
        gen_norm_value
    )
    _gen_norm_PM25_var = validator("PM25_var", allow_reuse=True, always=True)(
        gen_norm_value
    )
    _gen_norm_CO2_mean = validator("CO2_mean", allow_reuse=True, always=True)(
        gen_norm_value
    )
    _gen_norm_CO2_var = validator("CO2_var", allow_reuse=True, always=True)(
        gen_norm_value
    )
    _gen_norm_O3_mean = validator("O3_mean", allow_reuse=True, always=True)(
        gen_norm_value
    )
    _gen_norm_O3_var = validator("O3_var", allow_reuse=True, always=True)(
        gen_norm_value
    )
