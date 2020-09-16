from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, validator
from uuid import UUID
from ..types import FeatureNames, Source, Species


class StaticFeatureSchema(BaseModel):

    point_id: UUID
    feature_name: FeatureNames
    source: Source
    value_1000: float
    value_500: float
    value_200: float
    value_100: float
    value_10: float

    class Config:
        orm_mode = True

    def dict_enums(self, *args, **kwargs):
        """Return a dictionary like self.dict() but converts any enum types return their raw value"""

        dict_entries = []

        for field_name, value in self.dict(*args, **kwargs).items():
            if isinstance(value, Enum):
                dict_entries.append((field_name, value.value))
            else:
                dict_entries.append((field_name, value))
        return dict(dict_entries)

    def dict_flatten(self, *args, **kwargs):
        """Same as self.dict_enums except values and feature name
        are replaced with 'value_1000_{feature_name}
        """

        item = self.dict_enums(*args, **kwargs)

        new_dict = {}
        for key, value in item.items():
            if key in ("value", "feature_name"):
                continue
            if "value_" in key:
                new_key = f"{key}_{self.feature_name.value}"
                new_value = value
            else:
                new_key = key
                new_value = value

            new_dict[new_key] = new_value
        return new_dict


class StaticFeatureLocSchema(StaticFeatureSchema):

    lon: float
    lat: float


class StaticFeatureTimeSpecies(StaticFeatureLocSchema):

    measurement_start_utc: datetime
    epoch: Optional[int]
    species_code: Optional[Species]

    @validator("epoch", always=True)
    def gen_measurement_end_time(cls, v, values):
        "Generate end time one hour after start time"
        if v:
            raise ValidationError(
                "Dont pass a value for epoch. It is generated automatically"
            )
        return values["measurement_start_utc"].timestamp()


class StaticFeaturesWithSensors(StaticFeatureTimeSpecies):

    value: Optional[float]

    def dict_flatten(self, *args, **kwargs):
        """Same as self.dict_enums except values and feature name
        are replaced with 'value_1000_{feature_name}
        """

        item = self.dict_enums(*args, **kwargs)
        new_dict = {}
        for key, value in item.items():
            if key in ("value", "feature_name"):
                continue

            if "value_" in key:
                new_key = f"{key}_{self.feature_name.value}"
                new_value = value
            elif key == "species_code":
                new_key = f"{self.species_code}"
                new_value = self.value
            else:
                new_key = key
                new_value = value

            new_dict[new_key] = new_value

        return new_dict
