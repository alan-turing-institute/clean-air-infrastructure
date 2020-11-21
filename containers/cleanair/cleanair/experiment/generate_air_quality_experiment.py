"""Generate air quality experiments"""

from typing import List, Optional
from ..mixins import InstanceMixin
from ..params import default_svgp_model_params
from ..types import FeatureNames, ModelName, SVGPParams, Tag


def svgp_vary_static_features() -> List[InstanceMixin]:
    """Default SVGP with changing static features"""
    model_params = default_svgp_model_params()
    instance_list: List[InstanceMixin] = []
    # list of static features to iterate through
    static_features_list = [
        [],
        [FeatureNames.total_a_road_length],
    ]
    for static_features in static_features_list:
        # TODO create a data config from static_features
        data_config = ...
        # create instance and add to list
        instance = InstanceMixin(data_config, ModelName.svgp, model_params, tag=Tag.validation)
        instance_list.append(instance)
    return instance_list


def svgp_vary_num_inducing_points(num_inducing_points_list: Optional[List[int]] = None) -> List[InstanceMixin]:
    """Vary the number of inducing points in an SVGP"""
    data_config = ...
    instance_list = []
    num_inducing_points_list = [100, 200] if not num_inducing_points_list else num_inducing_points_list
    for num_inducing_points in num_inducing_points_list:
        model_params = default_svgp_model_params(num_inducing_points=num_inducing_points)
        instance = InstanceMixin(data_config, ModelName.svgp, model_params, tag=Tag.validation)
        instance_list.append(instance)
    return instance_list
