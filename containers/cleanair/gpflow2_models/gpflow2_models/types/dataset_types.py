"""Types for datasets."""

from typing import Dict, List, Tuple, Union, Optional
from datetime import datetime
from nptyping import NDArray, Float64, Int
from pydantic import BaseModel, validator
import numpy as np
from .enum_types import (
    Species,
    Source,
    StaticFeatureNames,
    FeatureBufferSize,
    DynamicFeatureNames,
)

Source = str
FeaturesDict = Dict[Source, np.ndarray]
IndexDict = Dict[Source, np.ndarray]
TargetDict = Dict[Source, Dict[Species, np.ndarray]]
NDArrayTuple = Tuple[np.ndarray, np.ndarray]
DatasetDict = Dict[str, Union[FeaturesDict, TargetDict]]
IndexedDatasetDict = Tuple[FeaturesDict, TargetDict, IndexDict]
InterestPointDict = Dict[Source, Union[str, List[str]]]
PredictionDict = Dict[Source, Dict[Species, Dict[str, np.ndarray]]]


class DataConfig(BaseModel):
    pass


class FullDataConfig(DataConfig):
    "Full configuration class"
    x_names: List[str]
    feature_names: List[str]

    # pylint: disable=E0213,R0201
    @validator("feature_names", each_item=True)
    def name_must_contain_space(cls, v):
        "Check value in name"
        parts = v.split("_")
        if parts[0] != "value":
            raise ValueError("must start with 'value_'")
        return v
