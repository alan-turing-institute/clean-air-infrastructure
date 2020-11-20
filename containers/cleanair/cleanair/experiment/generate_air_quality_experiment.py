"""Generate air quality experiments"""

from typing import List
from ..mixins import InstanceMixin
from .vary_air_quality_data_config import vary_static_features
from ..types import ModelName, SVGPParams

def svgp_vary_static_features() -> List[InstanceMixin]:
    """Default SVGP with changing static features"""
    data_config_list = vary_static_features()
    model_params = SVGPParams()
    instance_list: List[InstanceMixin] = []
    for data_config in data_config_list:
        instance = InstanceMixin(
            data_config,
            ModelName.svgp,
            model_params,
        )
        instance_list.append(instance)
    return instance_list
