"""Types for datasets."""

from typing import Dict, List, Tuple, Union
from datetime import datetime
from nptyping import NDArray, Float64, Int
from pydantic import BaseModel, validator
from .enum_types import (
    Species,
    Source,
    FeatureNames,
    FeatureBufferSize,
    DynamicFeatureNames,
)

# pylint: disable=invalid-name
FeaturesDict = Dict[Source, NDArray[Float64]]
IndexDict = Dict[Source, NDArray[Int]]
TargetDict = Dict[Source, Dict[Species, NDArray[Float64]]]
NDArrayTuple = Tuple[NDArray[Float64], NDArray[Float64]]
DatasetDict = Dict[str, Union[FeaturesDict, TargetDict]]
IndexedDatasetDict = Tuple[FeaturesDict, TargetDict, IndexDict]
InterestPointDict = Dict[Source, Union[str, List[str]]]


class DataConfig(BaseModel):
    "Base config for clean air models"
    train_start_date: datetime
    train_end_date: datetime
    pred_start_date: datetime
    pred_end_date: datetime
    include_prediction_y: bool
    train_sources: List[Source]
    pred_sources: List[Source]
    train_interest_points: InterestPointDict = {Source.laqn: "all"}
    pred_interest_points: InterestPointDict = {
        Source.laqn: "all",
        Source.hexgrid: "all",
    }
    species: List[Species]
    features: List[FeatureNames]
    dynamic_features: List[DynamicFeatureNames]
    buffer_sizes: List[FeatureBufferSize]
    norm_by: Source = Source.laqn


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
