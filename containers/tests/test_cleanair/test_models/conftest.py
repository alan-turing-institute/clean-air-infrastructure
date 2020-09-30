"""Fixtures for modelling."""

from datetime import timedelta
import pytest
import numpy as np
from cleanair.types import (
    BaseModelParams,
    DataConfig,
    FeatureNames,
    FeatureBufferSize,
    KernelParams,
    KernelType,
    ModelName,
    MRDGPParams,
    Source,
    Species,
)

#  pylint: disable=redefined-outer-name


@pytest.fixture(scope="function")
def mr_linear_params() -> KernelParams:
    """Matern 32 kernel params."""
    return KernelParams(
        name="mr_linear",
        type=KernelType.mr_linear,
        lengthscales=[1.0, 1.0, 1.0],
        variance=[1.0, 1.0, 1.0],
        ARD=True,
        active_dims=[0, 1, 2],
    )


@pytest.fixture(scope="function")
def sub_model(mr_linear_params: KernelParams) -> BaseModelParams:
    """Model params for sub-MRDGP"""
    return BaseModelParams(
        kernel=mr_linear_params,
        likelihood_variance=1.0,
        num_inducing_points=10,
        maxiter=10,
        minibatch_size=10,
    )


@pytest.fixture(scope="function")
def mrdgp_model_params(sub_model: BaseModelParams) -> MRDGPParams:
    """Create MRDGP model params."""
    return MRDGPParams(
        base_laqn=sub_model.copy(),
        base_sat=sub_model.copy(),
        dgp_sat=sub_model.copy(),
        mixing_weight=dict(name="dgp_only", param=None),
        num_prediction_samples=10,
        num_samples_between_layers=10,
    )


@pytest.fixture(scope="function")
def laqn_config(dataset_start_date, dataset_end_date):
    """LAQN dataset with just one feature."""
    return DataConfig(
        train_start_date=dataset_start_date,
        train_end_date=dataset_end_date,
        pred_start_date=dataset_end_date,
        pred_end_date=dataset_end_date + timedelta(days=2),
        include_prediction_y=False,
        train_sources=[Source.laqn],
        pred_sources=[Source.laqn],
        train_interest_points={Source.laqn.value: "all"},
        pred_interest_points={Source.laqn.value: "all"},
        species=[Species.NO2],
        features=[FeatureNames.total_a_road_length],
        buffer_sizes=[FeatureBufferSize.two_hundred],
        norm_by=Source.laqn,
        model_type=ModelName.svgp,
    )


@pytest.fixture(scope="function")
def sat_config(dataset_start_date):
    """Satellite dataset with no feature."""
    return DataConfig(
        train_start_date=dataset_start_date,
        train_end_date=dataset_start_date + timedelta(days=1),
        pred_start_date=dataset_start_date + timedelta(days=1),
        pred_end_date=dataset_start_date + timedelta(days=2),
        include_prediction_y=False,
        train_sources=[Source.laqn, Source.satellite],
        pred_sources=[Source.laqn],
        train_interest_points={Source.laqn.value: "all", Source.satellite.value: "all"},
        pred_interest_points={Source.laqn.value: "all", Source.satellite.value: "all"},
        species=[Species.NO2],
        features=[FeatureNames.total_a_road_length],
        buffer_sizes=[FeatureBufferSize.two_hundred],
        norm_by=Source.laqn,
        model_type=ModelName.mrdgp,
    )


@pytest.fixture(scope="function")
def laqn_full_config(laqn_config, model_config):
    """Generate full config for laqn."""
    model_config.validate_config(laqn_config)
    return model_config.generate_full_config(laqn_config)


@pytest.fixture(scope="function")
def laqn_training_data(laqn_full_config, model_data):
    training_data = model_data.download_config_data(
        laqn_full_config, training_data=True
    )
    return model_data.normalize_data(laqn_full_config, training_data)


@pytest.fixture(scope="function")
def laqn_test_data(laqn_full_config, model_data):
    test_data = model_data.download_prediction_config_data(laqn_full_config)
    return model_data.normalize_data(laqn_full_config, test_data)


@pytest.fixture(scope="function")
def sat_full_config(sat_config, model_config):
    """Generate full config for laqn + sat."""
    model_config.validate_config(sat_config)
    return model_config.generate_full_config(sat_config)


@pytest.fixture(scope="function")
def sat_training_data(sat_full_config, model_data):
    training_data = model_data.download_config_data(
        sat_full_config, training_data=True
    )
    return model_data.normalize_data(sat_full_config, training_data)


@pytest.fixture(scope="function")
def sat_test_data(sat_full_config, model_data):
    test_data = model_data.download_prediction_config_data(sat_full_config)
    return model_data.normalize_data(sat_full_config, test_data)
