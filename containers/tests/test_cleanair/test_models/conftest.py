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
