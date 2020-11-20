"""Fixtures for modelling."""

import pytest

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
