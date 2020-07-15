"""Types for datasets."""

from typing import Dict, List, Union
from nptyping import NDArray, Float64
from pydantic import BaseModel, validator
from datetime import datetime
from . import Species
from . import Source
from . import FeatureNames
from . import FeatureBufferSize

DataConfig = Dict[str, Union[str, bool, List[str]]]
FeaturesDict = Dict[Source, NDArray[Float64]]
TargetDict = Dict[Source, Dict[Species, NDArray[Float64]]]
DatasetDict = Dict[str, Union[FeaturesDict, TargetDict]]

InterestPointDict = Dict[Source, Union[str, List[str]]]


class BaseConfig(BaseModel):
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
    buffer_sizes: List[FeatureBufferSize]
    norm_by: Source = Source.laqn
    model_type: str


class FullConfig(BaseConfig):
    x_names: List[str]
    feature_names: List[str]

    @validator("feature_names", each_item=True)
    def name_must_contain_space(cls, v):

        parts = v.split("_")
        if parts[0] != "value":
            raise ValueError("must start with 'value_'")
        return v
