"""Types for datasets."""

from typing import Dict, List, Tuple, Union
from datetime import datetime
import numpy as np
import numpy.typing as npt
from pydantic import BaseModel, validator
from .enum_types import (
    Species,
    Source,
    StaticFeatureNames,
    FeatureBufferSize,
    DynamicFeatureNames,
)

# pylint: disable=invalid-name
FeaturesDict = Dict[Source, npt.NDArray[np.float64]]
IndexDict = Dict[Source, npt.NDArray[np.int_]]
TargetDict = Dict[Source, Dict[Species, npt.NDArray[np.float64]]]
NDArrayTuple = Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]
DatasetDict = Dict[str, Union[FeaturesDict, TargetDict]]
IndexedDatasetDict = Tuple[FeaturesDict, TargetDict, IndexDict]
InterestPointDict = Dict[Source, Union[str, List[str]]]
PredictionDict = Dict[Source, Dict[Species, Dict[str, npt.NDArray[np.float64]]]]


class DataConfig(BaseModel):
    "Base config for clean air models"
    train_start_date: datetime
    train_end_date: datetime
    pred_start_date: datetime
    pred_end_date: datetime
    include_prediction_y: bool
    train_sources: List[Source]
    pred_sources: List[Source]
    train_interest_points: InterestPointDict = {
        Source.laqn: "all",
        Source.breathe: "all",
        Source.satellite: "all",
    }
    pred_interest_points: InterestPointDict = {
        Source.laqn: "all",
        Source.hexgrid: "all",
        Source.breathe: "all",
        Source.satellite: "all",
    }
    species: List[Species]
    static_features: List[StaticFeatureNames]
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
