"""Fixtures for modelling."""

from datetime import timedelta
import pytest
from cleanair.types import (
    DataConfig,
    FeatureNames,
    FeatureBufferSize,
    ModelName,
    Source,
    Species,
)

#  pylint: disable=redefined-outer-name


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
