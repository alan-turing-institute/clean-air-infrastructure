"""Name and types for experiments"""

from enum import Enum


class ExperimentName(str, Enum):
    """Valid names of experiments"""

    vary_static_features = "vary_static_features"
