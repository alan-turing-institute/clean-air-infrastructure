"""
PydanticModels for serialising database query results
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

# pylint: disable=R0201,C0115,E0213

from pydantic import BaseModel, validator, ValidationError

from cleanair.types import StaticFeatureNames, DynamicFeatureNames, Source, Species


class BaseFeatures(BaseModel):

    point_id: UUID
    value_1000: float
    value_500: float
    value_200: float
    value_100: float
    value_10: float

    class Config:
        orm_mode = True

    def dict_enums(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Return a dictionary like self.dict() but converts any enum types return their raw value"""

        dict_entries = []

        for field_name, value in self.dict(*args, **kwargs).items():
            if isinstance(value, Enum):
                dict_entries.append((field_name, value.value))
            else:
                dict_entries.append((field_name, value))
        return dict(dict_entries)


class DynamicFeatureSchema(BaseFeatures):
    "Dynamic feature schema"

    feature_name: DynamicFeatureNames
    measurement_start_utc: datetime
    epoch: Optional[int]

    @validator("epoch", always=True)
    def gen_measurement_end_time(cls: Any, v: Any, values: Any) -> Any:
        "Generate end time one hour after start time"
        if v:
            raise ValidationError(
                "Dont pass a value for epoch. It is generated automatically", cls
            )
        return values["measurement_start_utc"].timestamp()

    class Config:
        orm_mode = True

    def dict_flatten(self, *args: str, **kwargs: bool) -> Dict:
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


class StaticFeatureSchema(BaseFeatures):
    """Static Features Schema"""

    feature_name: StaticFeatureNames
    source: Source
    in_london: bool

    class Config:
        orm_mode = True

    def dict_flatten(self, *args: str, **kwargs: bool) -> Dict:
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
    """Static Features Schema with lon and lat"""

    lon: float
    lat: float


class StaticFeatureTimeSpecies(StaticFeatureLocSchema):
    """Static Features Schema with measurement_start_utc, epoch and species_code"""

    measurement_start_utc: datetime
    species_code: Species
    epoch: Optional[int]

    @validator("epoch", always=True)
    def gen_measurement_end_time(cls: Any, v: Any, values: Any) -> Any:
        "Generate end time one hour after start time"
        if v:
            raise ValidationError(
                "Dont pass a value for epoch. It is generated automatically", cls
            )
        return values["measurement_start_utc"].timestamp()


class StaticFeaturesWithSensors(StaticFeatureTimeSpecies):
    """Static Features Schema with sensor reading and optional box_id"""

    value: Optional[float]
    box_id: Optional[UUID]

    def dict_flatten(self, *args: str, **kwargs: bool) -> Dict:
        """Same as self.dict_enums except values and feature name
        are replaced with 'value_1000_{feature_name}
        """

        def flatten_entries(key: str, value: bool) -> Any:
            "Helper function for flattening values"
            if "value_" in key:
                return (f"{key}_{self.feature_name.value}", value)
            if key == "species_code":
                return (f"{self.species_code}", self.value)
            return (key, value)

        item = self.dict_enums(*args, **kwargs)

        new_dict = dict(
            filter(
                lambda x: (x[0] not in ("value", "feature_name")),
                map(lambda x: flatten_entries(x[0], x[1]), item.items()),
            )
        )

        # Only give box_id for satellite type
        if self.source != Source.satellite:
            new_dict.pop("box_id")

        return new_dict
