"""Types for datasets."""

from typing import Dict, List, Union
from nptyping import NDArray, Float64

DataConfig = Dict[str, Union[str, bool, List[str]]]
FeaturesDict = Dict[str, NDArray[Float64]]
TargetDict = Dict[str, Dict[str, NDArray[Float64]]]
DatasetDict = Dict[str, Union[FeaturesDict, TargetDict]]
