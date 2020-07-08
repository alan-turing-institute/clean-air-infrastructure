"""Types for datasets."""

from typing import Dict, List, Union
from nptyping import NDArray, Float64
from pydantic import BaseModel
from datetime import datetime
from .copernicus_types import Species
from .sources import Source

DataConfig = Dict[str, Union[str, bool, List[str]]]
FeaturesDict = Dict[str, NDArray[Float64]]
TargetDict = Dict[str, Dict[str, NDArray[Float64]]]
DatasetDict = Dict[str, Union[FeaturesDict, TargetDict]]


class BaseConfig(BaseModel):
    train_start_date: datetime
    train_end_date: datetime
    pred_start_date: datetime
    pred_end_date: datetime
    include_prediction_y: bool
    train_sources: List[Source]
    pred_sources: List[Source]
    train_interest_points: Union[str, List[str]] = "all"
    train_satellite_interest_points: Union[str, List[str]] = "all"
    pred_interest_points: Union[str, List[str]] = "all"
    species: List[Species]
    features: List[str]
    norm_by: Source = Source.laqn
    model_type: str


class FullConfig(BaseConfig):
    x_names: List[str]
    feature_names: List[str]
