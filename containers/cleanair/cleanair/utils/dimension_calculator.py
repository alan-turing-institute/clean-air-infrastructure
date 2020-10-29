"""Calculate the input dimension of data"""

from ..types import FullDataConfig


def total_num_features(data_config: FullDataConfig) -> int:
    """Calculate number of features"""
    num_space_dimensions = 2
    num_time_dimensions = 1
    num_static_features = len(data_config.feature_names)
    num_dynamic_features = 0  # TODO once SCOOT is ready get num dynamic features
    return (
        num_static_features
        + num_dynamic_features
        + num_space_dimensions
        + num_time_dimensions
    )
