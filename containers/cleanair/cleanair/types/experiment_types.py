"""Name and types for experiments"""

from enum import Enum


class ExperimentName(str, Enum):
    """Valid names of experiments"""

    svgp_vary_static_features = "svgp_vary_static_features"
