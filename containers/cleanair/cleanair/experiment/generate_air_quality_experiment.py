"""Generate air quality experiments"""

from typing import List, Optional
from ..mixins import InstanceMixin
from ..models import ModelConfig
from ..params import default_svgp_model_params
from ..types import FeatureNames, ModelName, Tag
from .default_air_quality_data_config import default_laqn_data_config

# list of static features to iterate through
STATIC_FEATURES_LIST = [
    # [],   # BUG empty features cause error when downloading
    [FeatureNames.total_a_road_length],
    [FeatureNames.water],
    [FeatureNames.park],
    [FeatureNames.total_a_road_length, FeatureNames.water, FeatureNames.park],
]


def svgp_vary_static_features(secretfile: str) -> List[InstanceMixin]:
    """Default SVGP with changing static features"""
    # default model parameters for every model
    model_params = default_svgp_model_params()
    instance_list: List[InstanceMixin] = []

    model_config = ModelConfig(secretfile=secretfile)
    for static_features in STATIC_FEATURES_LIST:
        # create a data config from static_features
        data_config = default_laqn_data_config()
        data_config.features = static_features
        model_config.validate_config(data_config)
        full_data_config = model_config.generate_full_config(data_config)

        # create instance and add to list
        instance = InstanceMixin(
            full_data_config, ModelName.svgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)
    return instance_list


def svgp_vary_num_inducing_points(
    num_inducing_points_list: Optional[List[int]] = None,
) -> List[InstanceMixin]:
    """Vary the number of inducing points in an SVGP"""
    data_config = ...
    instance_list = []
    num_inducing_points_list = (
        [100, 200] if not num_inducing_points_list else num_inducing_points_list
    )
    for num_inducing_points in num_inducing_points_list:
        model_params = default_svgp_model_params(
            num_inducing_points=num_inducing_points
        )
        instance = InstanceMixin(
            data_config, ModelName.svgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)
    return instance_list
