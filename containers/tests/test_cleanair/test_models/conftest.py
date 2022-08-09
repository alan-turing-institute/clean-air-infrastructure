"""Fixtures for modelling."""
import numpy as np
import numpy.typing as npt
import pytest
from cleanair.types import (
    FeaturesDict,
    Source,
    Species,
    TargetDict,
)


#  pylint: disable=redefined-outer-name


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
def x_features(number_of_samples: int) -> npt.NDArray[np.float64]:
    """Features"""
    # return np.arange((number_of_samples, 1)).reshape((number_of_samples, 3)).astype(np.float)
    return (
        np.arange(number_of_samples * 3)
        .reshape((number_of_samples, 3))
        .astype(np.float)
    )


@pytest.fixture(scope="function")
def y_observations(
    x_features: npt.NDArray[np.float64], number_of_samples: int
) -> npt.NDArray[np.float64]:
    """Observations"""
    # only use first dimension to calculate feature
    return np.sin(2 * np.pi * x_features[:, 0] / float(number_of_samples)).reshape(
        (number_of_samples, 1)
    )


@pytest.fixture(scope="function")
def x_train(x_features) -> FeaturesDict:
    """A small training set of features"""
    return {
        Source.laqn: x_features,
    }


@pytest.fixture(scope="function")
def y_train(y_observations: npt.NDArray[np.float64]) -> TargetDict:
    """Small number of observations in dictionary structure"""
    return {
        Source.laqn: {
            Species.NO2: y_observations,
        }
    }


@pytest.fixture(scope="function")
def y_cleaning_array() -> np.array:
    return np.array(
        [[1.0], [2.0], [3.0], [4.0], [np.nan], [np.nan], [np.nan], [np.nan], [9.0]],
        np.float64,
    )


@pytest.fixture(scope="function")
def x_cleaning_array() -> np.array:
    return np.array(
        [
            [1.0, 1.0],
            [2.0, np.nan],
            [np.nan, 3.0],
            [np.nan, np.nan],
            [5.0, 5.0],
            [6.0, np.nan],
            [np.nan, 7.0],
            [np.nan, np.nan],
            [9.0, 9.0],
        ],
        np.float64,
    )
