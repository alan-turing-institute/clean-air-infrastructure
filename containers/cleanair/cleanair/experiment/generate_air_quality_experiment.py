"""Generate air quality experiments"""

from typing import List, Optional
from ..mixins import InstanceMixin
from ..models import ModelConfig
from ..params import default_svgp_model_params, default_mrdgp_model_params
from ..types import StaticFeatureNames, ModelName, Tag, FeatureBufferSize, Source
from .default_air_quality_data_config import (
    default_laqn_data_config,
    default_sat_data_config,
)

# list of static features to iterate through
STATIC_FEATURES_LIST = [
    [],
    [StaticFeatureNames.total_a_road_length],
    [StaticFeatureNames.water],
    [StaticFeatureNames.park],
    [
        StaticFeatureNames.total_a_road_length,
        StaticFeatureNames.water,
        StaticFeatureNames.park,
    ],
]


def _get_svgp_kernel_settings(feature_list):
    """Return input_dim and active_dims for SVGP model_params."""
    if len(feature_list) == 0:
        active_dims = [0, 1, 2]  # work around so that no features are used
        feature_list = [
            StaticFeatureNames.park
        ]  # tempory feature which wont be used by model
        input_dim = 3
    else:
        active_dims = None  # use all features
        input_dim = len(feature_list)

    return feature_list, input_dim, active_dims


def enumerate_enum(enum):
    """Return all possibilities of an enum."""
    return [e for e in enum]


def cached_instance(secretfile: str) -> List[InstanceMixin]:
    """Instance will features and sources. Used as a cached dataset."""

    instance_list: List[InstanceMixin] = []

    model_config = ModelConfig(secretfile=secretfile)
    data_config = default_sat_data_config()

    # get all features and sources
    static_features = enumerate_enum(StaticFeatureNames)
    buffer_sizes = enumerate_enum(FeatureBufferSize)
    train_sources = [Source.laqn, Source.satellite]
    pred_sources = [Source.laqn, Source.hexgrid]

    # create a data config from static_features
    data_config.buffer_sizes = buffer_sizes
    data_config.static_features = static_features
    data_config.train_sources = train_sources
    data_config.pred_sources = pred_sources

    # ensure valid config and data is available
    model_config.validate_config(data_config)

    full_data_config = model_config.generate_full_config(data_config)

    # SVGP as a tempory model just to create the instance
    static_features, input_dim, active_dims = _get_svgp_kernel_settings(static_features)
    model_params = default_svgp_model_params(
        active_dims=active_dims, input_dim=input_dim
    )

    # create instance and add to list
    instance = InstanceMixin(
        full_data_config, ModelName.svgp, model_params, tag=Tag.validation
    )
    instance_list.append(instance)

    return instance_list


def svgp_vary_static_features(secretfile: str) -> List[InstanceMixin]:
    """Default SVGP with changing static features"""
    # default model parameters for every model
    instance_list: List[InstanceMixin] = []

    model_config = ModelConfig(secretfile=secretfile)
    for static_features in STATIC_FEATURES_LIST:
        if len(static_features) == 0:
            active_dims = [0, 1, 2]  # work around so that no features are used
            static_features = [
                StaticFeatureNames.park
            ]  # tempory feature which wont be used by model
            input_dim = 3
        else:
            active_dims = None  # use all features
            input_dim = len(static_features)

        model_params = default_svgp_model_params(
            active_dims=active_dims, input_dim=input_dim
        )

        # create a data config from static_features
        data_config = default_laqn_data_config()
        data_config.static_features = static_features
        # model_config.validate_config(data_config)
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


def dgp_vary_static_features(secretfile: str) -> List[InstanceMixin]:
    """Default DGP with changing static features"""

    instance_list: List[InstanceMixin] = []

    model_config = ModelConfig(secretfile=secretfile)
    data_config = default_sat_data_config()

    for static_features in STATIC_FEATURES_LIST:
        n_features = len(static_features)
        # default model parameters for every model
        if len(static_features) == 0:
            static_features = [
                StaticFeatureNames.park
            ]  # tempory feature which wont be used by model
        # add 3 for epoch, lat, lon
        n_features = 3 + n_features
        model_params = default_mrdgp_model_params(n_features=n_features)

        # create a data config from static_features
        data_config.static_features = static_features
        full_data_config = model_config.generate_full_config(data_config)

        # create instance and add to list
        instance = InstanceMixin(
            full_data_config, ModelName.mrdgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)

    return instance_list
