"""Types for datasets."""

from typing import Dict, List, Tuple, Union
from nptyping import NDArray, Float64

# pylint: disable=invalid-name

DataConfig = Dict[str, Union[str, bool, List[str]]]
FeaturesDict = Dict[str, NDArray[Float64]]
NDArrayTuple = Tuple(NDArray[Float64], NDArray[Float64])
TargetDict = Dict[str, Dict[str, NDArray[Float64]]]
DatasetDict = Dict[str, Union[FeaturesDict, TargetDict]]
