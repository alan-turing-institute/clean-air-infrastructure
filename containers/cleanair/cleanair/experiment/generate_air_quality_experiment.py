"""Generate air quality experiments.

Experiments go through 3 stages:
1. "Vary" means a somewhat brute force approach
2. "Tuning" means we are beginning to understand which params are good
3. "Production" means we think this is the best parameter setup
"""

from datetime import timedelta
import itertools

from typing import List
from ..params.shared_params import (
    PRODUCTION_BUFFER_SIZES,
    PRODUCTION_DYNAMIC_FEATURES,
    PRODUCTION_STATIC_FEATURES,
)
from ..params.svgp_params import (
    PRODUCTION_SVGP_FORECAST_INTEREST_POINTS,
    PRODUCTION_SVGP_FORECAST_SOURCES,
    PRODUCTION_SVGP_SPECIES,
    PRODUCTION_SVGP_TRAIN_DAYS,
    PRODUCTION_SVGP_TRAIN_INTEREST_POINTS,
    PRODUCTION_SVGP_TRAIN_SOURCES,
)
from ..types.dataset_types import DataConfig
from ..types.enum_types import ClusterId
from ..utils import total_num_features
from ..mixins import InstanceMixin
from ..models import ModelConfig
from ..params import (
    default_svgp_model_params,
    default_mrdgp_model_params,
    PRODUCTION_FORECAST_DAYS,
    PRODUCTION_MRDGP_SPECIES,
    PRODUCTION_MRDGP_FORECAST_INTEREST_POINTS,
    PRODUCTION_MRDGP_FORECAST_SOURCES,
    PRODUCTION_MRDGP_TRAIN_DAYS,
    PRODUCTION_MRDGP_TRAIN_INTEREST_POINTS,
    PRODUCTION_MRDGP_TRAIN_SOURCES,
)
from ..timestamps import datetime_from_word
from ..types import StaticFeatureNames, ModelName, Tag, FeatureBufferSize, Source
from .default_air_quality_data_config import (
    default_laqn_data_config,
    default_sat_data_config,
)

# list used in varying inducing points experiments
TUNING_STATIC_FEATURES = [
    [StaticFeatureNames.total_a_road_primary_length, StaticFeatureNames.flat],
    [
        StaticFeatureNames.total_a_road_length,
        StaticFeatureNames.total_a_road_primary_length,
        StaticFeatureNames.flat,
        StaticFeatureNames.max_canyon_ratio,
    ],
]

# for the "vary static features" experiments, we evaluate how effective different static features are
VARY_STATIC_FEATURES = [
    [],
    [StaticFeatureNames.flat],
    [StaticFeatureNames.max_canyon_ratio],
    [StaticFeatureNames.park],
    [StaticFeatureNames.total_a_road_length],
    [StaticFeatureNames.total_a_road_primary_length],
    [StaticFeatureNames.water],
    [StaticFeatureNames.total_a_road_primary_length, StaticFeatureNames.flat],
    [
        StaticFeatureNames.park,
        StaticFeatureNames.total_a_road_primary_length,
        StaticFeatureNames.flat,
        StaticFeatureNames.max_canyon_ratio,
    ],
]

# vary the size of the buffer around an interest point for different granularity
VARY_BUFFER_SIZES = [
    [FeatureBufferSize.one_hundred],
    [FeatureBufferSize.two_hundred],
    [FeatureBufferSize.five_hundred],
    [FeatureBufferSize.one_thousand],
    [FeatureBufferSize.one_hundred, FeatureBufferSize.five_hundred],
    [FeatureBufferSize.two_hundred, FeatureBufferSize.one_thousand],
]


VARY_LENGTHSCALES = [0.01, 0.1, 1.0]
VARY_LIKELIHOOD_VARIANCE = [5.0]


def __static_features_fix(data_config: DataConfig) -> DataConfig:
    """Hack for a bug that occurs when the list of static features is empty.

    If the list of static features is empty, add a park feature."""
    data_config.static_features = [StaticFeatureNames.park]
    return data_config


def production_svgp_static(secretfile: str) -> List[InstanceMixin]:
    """The production version of the static SVGP"""
    train_upto = datetime_from_word("today")
    train_start = train_upto - timedelta(PRODUCTION_SVGP_TRAIN_DAYS)
    forecast_upto = train_upto + timedelta(PRODUCTION_FORECAST_DAYS)
    data_config = DataConfig(
        train_start_date=train_start,
        train_end_date=train_upto,
        pred_start_date=train_upto,
        pred_end_date=forecast_upto,
        include_prediction_y=True,
        train_sources=PRODUCTION_SVGP_TRAIN_SOURCES,
        pred_sources=PRODUCTION_SVGP_FORECAST_SOURCES,
        train_interest_points=PRODUCTION_SVGP_TRAIN_INTEREST_POINTS,
        pred_interest_points=PRODUCTION_SVGP_FORECAST_INTEREST_POINTS,
        species=PRODUCTION_SVGP_SPECIES,
        static_features=PRODUCTION_STATIC_FEATURES,
        dynamic_features=[],
        buffer_sizes=PRODUCTION_BUFFER_SIZES,
        norm_by=Source.laqn,
    )

    input_dim = total_num_features(data_config)
    active_dims = list(range(input_dim))  # explicitly calculate active dims

    model_config = ModelConfig(secretfile=secretfile)
    model_config.validate_config(data_config)
    full_data_config = model_config.generate_full_config(data_config)

    # create model params and change
    model_params = default_svgp_model_params(
        active_dims=active_dims, input_dim=input_dim,
    )

    # create instance and add to list
    instance = InstanceMixin(
        full_data_config,
        ModelName.svgp,
        model_params,
        tag=Tag.production,
        cluster_id=ClusterId.nc6,
    )
    return [instance]


def production_svgp_dynamic(secretfile: str) -> List[InstanceMixin]:
    """The production version of the dynamic SVGP"""
    train_upto = datetime_from_word("today")
    train_start = train_upto - timedelta(PRODUCTION_SVGP_TRAIN_DAYS)
    forecast_upto = train_upto + timedelta(PRODUCTION_FORECAST_DAYS)
    data_config = DataConfig(
        train_start_date=train_start,
        train_end_date=train_upto,
        pred_start_date=train_upto,
        pred_end_date=forecast_upto,
        include_prediction_y=True,
        train_sources=PRODUCTION_SVGP_TRAIN_SOURCES,
        pred_sources=PRODUCTION_SVGP_FORECAST_SOURCES,
        train_interest_points=PRODUCTION_SVGP_TRAIN_INTEREST_POINTS,
        pred_interest_points=PRODUCTION_SVGP_FORECAST_INTEREST_POINTS,
        species=PRODUCTION_SVGP_SPECIES,
        static_features=PRODUCTION_STATIC_FEATURES,
        dynamic_features=PRODUCTION_DYNAMIC_FEATURES,
        buffer_sizes=PRODUCTION_BUFFER_SIZES,
        norm_by=Source.laqn,
    )

    input_dim = total_num_features(data_config)
    active_dims = list(range(input_dim))  # explicitly calculate active dims

    model_config = ModelConfig(secretfile=secretfile)
    model_config.validate_config(data_config)
    full_data_config = model_config.generate_full_config(data_config)

    # create model params and change
    model_params = default_svgp_model_params(
        active_dims=active_dims, input_dim=input_dim,
    )

    # create instance and add to list
    instance = InstanceMixin(
        full_data_config,
        ModelName.svgp,
        model_params,
        tag=Tag.production,
        cluster_id=ClusterId.nc6,
    )
    return [instance]


def production_mrdgp_static(secretfile: str) -> List[InstanceMixin]:
    """The production version of the dynamic MRDGP"""
    train_upto = datetime_from_word("today")
    train_start = train_upto - timedelta(PRODUCTION_MRDGP_TRAIN_DAYS)
    forecast_upto = train_upto + timedelta(PRODUCTION_FORECAST_DAYS)
    data_config = DataConfig(
        train_start_date=train_start,
        train_end_date=train_upto,
        pred_start_date=train_upto,
        pred_end_date=forecast_upto,
        include_prediction_y=True,
        train_sources=PRODUCTION_MRDGP_TRAIN_SOURCES,
        pred_sources=PRODUCTION_MRDGP_FORECAST_SOURCES,
        train_interest_points=PRODUCTION_MRDGP_TRAIN_INTEREST_POINTS,
        pred_interest_points=PRODUCTION_MRDGP_FORECAST_INTEREST_POINTS,
        species=PRODUCTION_MRDGP_SPECIES,
        static_features=PRODUCTION_STATIC_FEATURES,
        dynamic_features=[],
        buffer_sizes=PRODUCTION_BUFFER_SIZES,
        norm_by=Source.laqn,
    )

    input_dim = total_num_features(data_config)

    model_config = ModelConfig(secretfile=secretfile)
    model_config.validate_config(data_config)
    full_data_config = model_config.generate_full_config(data_config)

    # create model params
    model_params = default_mrdgp_model_params(input_dim)

    # create instance and add to list
    instance = InstanceMixin(
        full_data_config,
        ModelName.mrdgp,
        model_params,
        tag=Tag.production,
        cluster_id=ClusterId.nc6,
    )
    return [instance]


def production_mrdgp_dynamic(secretfile: str, cluster_id: ClusterId = ClusterId.nc6) -> List[InstanceMixin]:
    """The production version of the dynamic MRDGP"""
    train_upto = datetime_from_word("today")
    train_start = train_upto - timedelta(PRODUCTION_MRDGP_TRAIN_DAYS)
    forecast_upto = train_upto + timedelta(PRODUCTION_FORECAST_DAYS)
    data_config = DataConfig(
        train_start_date=train_start,
        train_end_date=train_upto,
        pred_start_date=train_upto,
        pred_end_date=forecast_upto,
        include_prediction_y=True,
        train_sources=PRODUCTION_MRDGP_TRAIN_SOURCES,
        pred_sources=PRODUCTION_MRDGP_FORECAST_SOURCES,
        train_interest_points=PRODUCTION_MRDGP_TRAIN_INTEREST_POINTS,
        pred_interest_points=PRODUCTION_MRDGP_FORECAST_INTEREST_POINTS,
        species=PRODUCTION_MRDGP_SPECIES,
        static_features=PRODUCTION_STATIC_FEATURES,
        dynamic_features=PRODUCTION_DYNAMIC_FEATURES,
        buffer_sizes=PRODUCTION_BUFFER_SIZES,
        norm_by=Source.laqn,
    )

    input_dim = total_num_features(data_config)

    model_config = ModelConfig(secretfile=secretfile)
    model_config.validate_config(data_config)
    full_data_config = model_config.generate_full_config(data_config)

    # create model params
    model_params = default_mrdgp_model_params(input_dim)

    # create instance and add to list
    instance = InstanceMixin(
        full_data_config,
        ModelName.mrdgp,
        model_params,
        tag=Tag.production,
        cluster_id=cluster_id,
    )
    return [instance]


def svgp_vary_standard(secretfile: str) -> List[InstanceMixin]:
    """Default SVGP with changing static features"""
    # default model parameters for every model
    instance_list: List[InstanceMixin] = []

    num_z = 1000
    maxiter = 10000

    model_config = ModelConfig(secretfile=secretfile)

    for static_features, lengthscale, sig_y in itertools.product(
        TUNING_STATIC_FEATURES, VARY_LENGTHSCALES, VARY_LIKELIHOOD_VARIANCE,
    ):
        # create data config
        data_config = default_laqn_data_config()
        data_config.static_features = static_features
        data_config.buffer_sizes = PRODUCTION_BUFFER_SIZES

        input_dim = total_num_features(data_config)
        active_dims = list(range(input_dim))  # explicitly calculate active dims
        data_config = __static_features_fix(data_config)

        model_config.validate_config(data_config)
        full_data_config = model_config.generate_full_config(data_config)

        # create model params and change
        model_params = default_svgp_model_params(
            num_inducing_points=num_z,
            maxiter=maxiter,
            active_dims=active_dims,
            input_dim=input_dim,
            lengthscales=lengthscale,
            likelihood_variance=sig_y,
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
    maxiter = 10000

    model_config = ModelConfig(secretfile=secretfile)

    for static_features, lengthscale, sig_y in itertools.product(
        TUNING_STATIC_FEATURES, VARY_LENGTHSCALES, VARY_LIKELIHOOD_VARIANCE,
    ):
        # create a data config from static_features
        data_config = default_sat_data_config()
        data_config.buffer_sizes = PRODUCTION_BUFFER_SIZES
        data_config.static_features = static_features
        n_features = total_num_features(data_config)
        data_config = __static_features_fix(data_config)
        full_data_config = model_config.generate_full_config(data_config)

        model_params = default_mrdgp_model_params(
            n_features=n_features,
            num_inducing_points=num_z,
            maxiter=maxiter,
            lengthscales=lengthscale,
            likelihood_variance=sig_y,
        )

        # create instance and add to list
        instance = InstanceMixin(
            full_data_config, ModelName.mrdgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)

    return instance_list


def cached_instance(secretfile: str) -> List[InstanceMixin]:
    """Instance will features and sources. Used as a cached dataset."""

    instance_list: List[InstanceMixin] = []

    model_config = ModelConfig(secretfile=secretfile)
    data_config = default_sat_data_config()

    # get all features and sources
    data_config.buffer_sizes = list(FeatureBufferSize)
    data_config.static_features = list(StaticFeatureNames)
    data_config.train_sources = [Source.laqn, Source.satellite]
    data_config.pred_sources = [Source.laqn, Source.hexgrid]
    input_dim = total_num_features(data_config)
    active_dims = list(range(input_dim))

    # ensure valid config and data is available
    model_config.validate_config(data_config)
    full_data_config = model_config.generate_full_config(data_config)

    # SVGP as a tempory model just to create the instance
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
    """Default SVGP with changing static features and buffer sizes"""
    instance_list: List[InstanceMixin] = []
    model_config = ModelConfig(secretfile=secretfile)
    for static_features in itertools.product(VARY_STATIC_FEATURES, VARY_BUFFER_SIZES):
        # create a data config from static_features
        data_config = default_laqn_data_config()
        data_config.static_features = static_features

        # get num features - if no static features then add 'fake' feature
        input_dim = total_num_features(data_config)
        active_dims = list(range(input_dim))
        data_config = __static_features_fix(data_config)

        # ensure the data settings are valid
        model_config.validate_config(data_config)
        full_data_config = model_config.generate_full_config(data_config)

        # get the model params for the given data settings
        model_params = default_svgp_model_params(
            active_dims=active_dims, input_dim=input_dim
        )

        # create instance and add to list
        instance = InstanceMixin(
            full_data_config, ModelName.svgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)
    return instance_list


def svgp_vary_num_inducing_points(secretfile: str) -> List[InstanceMixin]:
    """Vary the number of inducing points in an SVGP"""
    instance_list: List[InstanceMixin] = []
    model_config = ModelConfig(secretfile=secretfile)

    data_config = default_laqn_data_config()
    data_config.buffer_sizes = PRODUCTION_BUFFER_SIZES
    data_config.static_features = PRODUCTION_STATIC_FEATURES

    # get num features - if no static features then add 'fake' feature
    input_dim = total_num_features(data_config)
    active_dims = list(range(input_dim))
    data_config = __static_features_fix(data_config)

    # ensure the data settings are valid
    model_config.validate_config(data_config)
    full_data_config = model_config.generate_full_config(data_config)

    num_inducing_points_list = [100, 200, 500, 1000]
    for num_inducing_points in num_inducing_points_list:
        model_params = default_svgp_model_params(
            num_inducing_points=num_inducing_points,
            active_dims=active_dims,
            input_dim=input_dim,
        )
        instance = InstanceMixin(
            full_data_config, ModelName.svgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)
    return instance_list


def dgp_vary_static_features(secretfile: str) -> List[InstanceMixin]:
    """Default DGP with changing static features"""
    instance_list: List[InstanceMixin] = []
    model_config = ModelConfig(secretfile=secretfile)

    for static_features in VARY_STATIC_FEATURES:

        # create a data config from static_features
        data_config = default_sat_data_config()
        data_config.static_features = static_features
        n_features = total_num_features(data_config)
        data_config = __static_features_fix(data_config)

        # ensure the data settings are valid
        model_config.validate_config(data_config)
        full_data_config = model_config.generate_full_config(data_config)

        # create model parameters
        model_params = default_mrdgp_model_params(n_features=n_features)

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

    # create a data config from static_features
    data_config = default_sat_data_config()
    data_config.buffer_sizes = PRODUCTION_BUFFER_SIZES
    data_config.static_features = PRODUCTION_STATIC_FEATURES
    n_features = total_num_features(data_config)
    data_config = __static_features_fix(data_config)

    # ensure the data settings are valid
    model_config.validate_config(data_config)
    full_data_config = model_config.generate_full_config(data_config)

    # try all permutations of inducing points and max iterations
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

    # create a data config from static_features
    model_config = ModelConfig(secretfile=secretfile)
    data_config = default_sat_data_config()
    data_config.buffer_sizes = PRODUCTION_BUFFER_SIZES
    data_config.static_features = PRODUCTION_STATIC_FEATURES
    input_dim = total_num_features(data_config)  # calculate num features before fix
    data_config = __static_features_fix(data_config)
    full_data_config = model_config.generate_full_config(data_config)

    for num_z, maxiter in itertools.product(inducing_point_sizes, iters):
        model_params = default_mrdgp_model_params(
            n_features=input_dim, num_inducing_points=num_z, maxiter=maxiter
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

    # create a data config from static_features
    model_config = ModelConfig(secretfile=secretfile)
    data_config = default_laqn_data_config()
    data_config.buffer_sizes = PRODUCTION_BUFFER_SIZES
    data_config.static_features = PRODUCTION_STATIC_FEATURES
    input_dim = total_num_features(data_config)
    active_dims = list(range(input_dim))  # explicitly calculate active dims
    data_config = __static_features_fix(data_config)
    full_data_config = model_config.generate_full_config(data_config)

    for num_z, maxiter in itertools.product(inducing_point_sizes, iters):
        model_params = default_svgp_model_params(
            num_inducing_points=num_z,
            maxiter=maxiter,
            active_dims=active_dims,
            input_dim=input_dim,
        )

        # create instance and add to list
        instance = InstanceMixin(
            full_data_config, ModelName.svgp, model_params, tag=Tag.validation
        )
        instance_list.append(instance)

    return instance_list


def dryrun_svgp(secretfile: str) -> List[InstanceMixin]:
    """SVGP on just one day of training/test data with small
    inducing points and maxiter to make it run very fast"""
    model_config = ModelConfig(secretfile=secretfile)
    data_config = default_laqn_data_config()
    data_config.static_features = []
    data_config.dynamic_features = []
    data_config.train_sources = [Source.laqn]
    data_config.pred_sources = [Source.laqn]
    input_dim = total_num_features(data_config)
    active_dims = list(range(input_dim))  # explicitly calculate active dims
    data_config = __static_features_fix(data_config)
    full_data_config = model_config.generate_full_config(data_config)
    model_params = default_svgp_model_params(
        num_inducing_points=100,
        maxiter=100,
        active_dims=active_dims,
        input_dim=input_dim,
    )
    return [InstanceMixin(full_data_config, ModelName.svgp, model_params, tag=Tag.test)]
