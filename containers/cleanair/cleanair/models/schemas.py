from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from ..types import FeatureNames, Source, Species


class StaticFeatureSchema(BaseModel):

    point_id: UUID
    feature_name: FeatureNames
    feature_source: Source
    value_1000: float
    value_500: float
    value_200: float
    value_100: float
    value_10: float


class StaticFeatureLocSchema(StaticFeatureSchema):

    lon: float
    lat: float


class StaticFeatureTimeSpecies(StaticFeatureLocSchema):

    measurement_start_utc: datetime
    species_code: Species

    class Config:
        orm_mode = True
