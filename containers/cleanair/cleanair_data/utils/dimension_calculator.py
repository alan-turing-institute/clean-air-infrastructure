"""Calculate the input dimension of data"""

from ..types import DataConfig


def total_num_features(data_config: DataConfig) -> int:
    """Calculate number of features"""
    num_space_dimensions = 2
    num_time_dimensions = 1
    num_static_features = len(data_config.static_features) * len(
        data_config.buffer_sizes
    )
    num_dynamic_features = len(data_config.dynamic_features) * len(
        data_config.buffer_sizes
    )
    return (
        num_static_features
        + num_dynamic_features
        + num_space_dimensions
        + num_time_dimensions
    )
