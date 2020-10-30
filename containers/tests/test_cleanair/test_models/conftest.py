"""Fixtures for modelling."""

from datetime import timedelta
import numpy as np
from nptyping import NDArray, Float
import pytest
from cleanair.types import (
    DataConfig,
    FeaturesDict,
    FeatureNames,
    FeatureBufferSize,
    ModelName,
    Source,
    Species,
    TargetDict,
)

#  pylint: disable=redefined-outer-name


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
    """Training data for laqn."""
    training_data = model_data.download_config_data(
        laqn_full_config, training_data=True
    )
    return model_data.normalize_data(laqn_full_config, training_data)


@pytest.fixture(scope="function")
def laqn_test_data(laqn_full_config, model_data):
    """Test data for laqn."""
    test_data = model_data.download_prediction_config_data(laqn_full_config)
    return model_data.normalize_data(laqn_full_config, test_data)


@pytest.fixture(scope="function")
def sat_full_config(sat_config, model_config):
    """Generate full config for laqn + sat."""
    model_config.validate_config(sat_config)
    return model_config.generate_full_config(sat_config)


@pytest.fixture(scope="function")
def sat_training_data(sat_full_config, model_data):
    """Training data with satelllite and laqn"""
    training_data = model_data.download_config_data(sat_full_config, training_data=True)
    return model_data.normalize_data(sat_full_config, training_data)


@pytest.fixture(scope="function")
def sat_test_data(sat_full_config, model_data):
    """Test data with laqn."""
    test_data = model_data.download_prediction_config_data(sat_full_config)
    return model_data.normalize_data(sat_full_config, test_data)


@pytest.fixture(scope="function")
def number_of_samples() -> int:
    """Number of samples from sine wave"""
    return 200


@pytest.fixture(scope="function")
def x_features(number_of_samples: int) -> NDArray[Float]:
    """Features"""
    return np.arange(number_of_samples).reshape((number_of_samples, 1)).astype(np.float)


@pytest.fixture(scope="function")
def y_observations(
    x_features: NDArray[Float], number_of_samples: int
) -> NDArray[Float]:
    """Observations"""
    return np.sin(2 * np.pi * x_features / float(number_of_samples)).reshape(
        (number_of_samples, 1)
    )


@pytest.fixture(scope="function")
def x_train(x_features) -> FeaturesDict:
    """A small training set of features"""
    return {
        Source.laqn: x_features,
    }


@pytest.fixture(scope="function")
def y_train(y_observations: NDArray[Float]) -> TargetDict:
    """Small number of observations in dictionary structure"""
    return {Source.laqn: {Species.NO2: y_observations,}}
