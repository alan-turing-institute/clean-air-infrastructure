"""Name and types for experiments"""

from enum import Enum
from typing import List
from pydantic import BaseModel


class ExperimentName(str, Enum):
    """Valid names of experiments"""

    svgp_vary_static_features = "svgp_vary_static_features"
    dgp_vary_static_features = "dgp_vary_static_features"


class ExperimentConfig(BaseModel):
    """Settings for an experiment"""

    name: ExperimentName
    instance_id_list: List[str]
