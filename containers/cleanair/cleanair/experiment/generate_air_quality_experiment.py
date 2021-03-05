"""Generate air quality experiments"""

import itertools

from typing import List, Optional
from ..mixins import InstanceMixin
from ..models import ModelConfig
from ..params import default_svgp_model_params, default_mrdgp_model_params
from ..types import StaticFeatureNames, ModelName, Tag, FeatureBufferSize
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

# list used in varying inducing points experiments
STANDARD_FEATURES_LIST = [
    [
        StaticFeatureNames.total_a_road_primary_length,
        StaticFeatureNames.flat
    ],
    [
        StaticFeatureNames.total_a_road_length,
        StaticFeatureNames.total_a_road_primary_length,
        StaticFeatureNames.flat,
        StaticFeatureNames.max_canyon_ratio
    ]
]
STANDARD_BUFFER_SIZE = [FeatureBufferSize.two_hundred, FeatureBufferSize.one_hundred]

STANDARD_LENGTHSCALES = [0.01, 0.1, 1.0]
STANDARD_SIG_Y = [5.0]


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

def _get_dgp_kernel_settings(feature_list):
    """Return input_dim and active_dims for SVGP model_params."""
    n_features = len(feature_list)

    if len(feature_list) == 0:
        feature_list = [
            StaticFeatureNames.park
        ]  # tempory feature which wont be used by model


    #the DGP  uses n_features to construct active_dims and input_dim internally
    n_features = n_features + 3

    return feature_list, n_features


def svgp_vary_standard(secretfile: str) -> List[InstanceMixin]:
    """Default SVGP with changing static features"""
    # default model parameters for every model
    instance_list: List[InstanceMixin] = []

    num_z = 1000
    maxiter=10000

    model_config = ModelConfig(secretfile=secretfile)

    for features, buffer_size, lengthscale, sig_y in itertools.product(STANDARD_FEATURES_LIST, STANDARD_BUFFER_SIZE, STANDARD_LENGTHSCALES, STANDARD_SIG_Y):

        data_config = default_laqn_data_config()
        features, input_dim, active_dims = _get_svgp_kernel_settings(features)

        # create a data config from static_features
        data_config.buffer_sizes = [buffer_size]
        data_config.static_features = features

        #model_config.validate_config(data_config)
        

        full_data_config = model_config.generate_full_config(data_config)

        model_params = default_svgp_model_params(
            num_inducing_points=num_z, 
            maxiter=maxiter,
            active_dims=active_dims, 
            input_dim=input_dim,
            lengthscales=lengthscale,
            likelihood_variance=sig_y
        )

        # create instance and add to list
        instance = InstanceMixin(
            full_data_config, ModelName.svgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)

    return instance_list

def dgp_vary_standard(secretfile: str) -> List[InstanceMixin]:
    """Default SVGP with changing static features"""
    # default model parameters for every model
    instance_list: List[InstanceMixin] = []

    num_z = 300
    maxiter=10000

    model_config = ModelConfig(secretfile=secretfile)

    for features, buffer_size, lengthscale, sig_y in itertools.product(STANDARD_FEATURES_LIST, STANDARD_BUFFER_SIZE, STANDARD_LENGTHSCALES, STANDARD_SIG_Y):

        data_config = default_laqn_data_config()
        features, n_features = _get_dgp_kernel_settings(features)

        # create a data config from static_features
        data_config.buffer_sizes = [buffer_size]
        data_config.static_features = features

        #model_config.validate_config(data_config)

        full_data_config = model_config.generate_full_config(data_config)

        model_params = default_mrdgp_model_params(
            n_features = n_features,
            num_inducing_points=num_z, 
            maxiter=maxiter,
            lengthscales=lengthscale,
            likelihood_variance=sig_y
        )

        # create instance and add to list
        instance = InstanceMixin(
            full_data_config, ModelName.mrdgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)

    return instance_list

def svgp_vary_static_features(secretfile: str) -> List[InstanceMixin]:
    """Default SVGP with changing static features"""
    # default model parameters for every model
    instance_list: List[InstanceMixin] = []

    model_config = ModelConfig(secretfile=secretfile)
    for static_features in STATIC_FEATURES_LIST:
        static_features, input_dim, active_dims = _get_svgp_kernel_settings(static_features)

        model_params = default_svgp_model_params(
            active_dims=active_dims, input_dim=input_dim
        )

        # create a data config from static_features
        data_config = default_laqn_data_config()
        data_config.static_features = static_features
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


def dgp_vary_inducing_and_maxiter(secretfile: str) -> List[InstanceMixin]:
    """MRDGP with various combinations of number of inducing points and max iterations"""
    inducing_point_sizes = [100, 200, 500]
    iters = [1000, 5000, 10000]

    instance_list: List[InstanceMixin] = []

    model_config = ModelConfig(secretfile=secretfile)
    data_config = default_sat_data_config()
    static_features = STANDARD_FEATURES_LIST

    n_features = len(static_features)

    # default model parameters for every model
    if len(static_features) == 0:
        static_features = [
            StaticFeatureNames.park
        ]  # tempory feature which wont be used by model

    # add 3 for epoch, lat, lon
    n_features = 3 + n_features

    # create a data config from static_features
    data_config.static_features = static_features
    full_data_config = model_config.generate_full_config(data_config)

    for num_z, maxiter in itertools.product(inducing_point_sizes, iters):
        model_params = default_mrdgp_model_params(
            n_features=n_features, num_inducing_points=num_z, maxiter=maxiter
        )

        # create instance and add to list
        instance = InstanceMixin(
            full_data_config, ModelName.mrdgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)

    return instance_list


def dgp_small_inducing_and_maxiter(secretfile: str) -> List[InstanceMixin]:
    """MRDGP with a single combination of number of inducing points and max iterations"""
    # TODO: can probably refactor this and dgp_vary_inducing_and_maxiter
    inducing_point_sizes = [300]
    iters = [10000]

    instance_list: List[InstanceMixin] = []

    model_config = ModelConfig(secretfile=secretfile)
    data_config = default_sat_data_config()

    static_features = STANDARD_FEATURES_LIST
    buffer_sizes = STANDARD_BUFFER_SIZE

    n_features = len(static_features)

    # default model parameters for every model
    if len(static_features) == 0:
        active_dims = [0, 1, 2]  # work around so that no features are used
        static_features = [
            StaticFeatureNames.park
        ]  # tempory feature which wont be used by model
        input_dim = 3
    else:
        active_dims = None  # use all features
        input_dim = len(static_features)# tempory feature which wont be used by model

    # add 3 for epoch, lat, lon
    n_features = 3 + n_features

    # create a data config from static_features
    data_config.buffer_sizes = buffer_sizes
    data_config.static_features = static_features

    full_data_config = model_config.generate_full_config(data_config)

    for num_z, maxiter in itertools.product(inducing_point_sizes, iters):
        model_params = default_mrdgp_model_params(
            n_features=n_features, num_inducing_points=num_z, maxiter=maxiter
        )

        # create instance and add to list
        instance = InstanceMixin(
            full_data_config, ModelName.mrdgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)

    return instance_list

def svgp_small_inducing_and_maxiter(secretfile: str) -> List[InstanceMixin]:
    """SVGP with a single combination of number of inducing points and max iterations and on hexgrid"""
    inducing_point_sizes = [1000]
    iters = [10000]

    instance_list: List[InstanceMixin] = []

    model_config = ModelConfig(secretfile=secretfile)
    data_config = default_laqn_data_config()

    static_features = STANDARD_FEATURES_LIST
    buffer_sizes = STANDARD_BUFFER_SIZE


    static_features, input_dim, active_dims = _get_svgp_kernel_settings(static_features)

    # create a data config from static_features
    data_config.buffer_sizes = buffer_sizes
    data_config.static_features = static_features

    full_data_config = model_config.generate_full_config(data_config)

    for num_z, maxiter in itertools.product(inducing_point_sizes, iters):
        model_params = default_svgp_model_params(
            num_inducing_points=num_z, maxiter=maxiter,
            active_dims=active_dims, input_dim=input_dim
        )

        # create instance and add to list
        instance = InstanceMixin(
            full_data_config, ModelName.svgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)

    return instance_list
