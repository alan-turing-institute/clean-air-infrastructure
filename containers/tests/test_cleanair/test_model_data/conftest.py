"""Fixtures for the model data class."""

from typing import Iterable
from datetime import timedelta
import pytest
from pydantic import BaseModel
import numpy as np
from cleanair.types import FeaturesDict, TargetDict
from cleanair.databases.tables import (
    StaticFeature,
    LAQNReading,
    LAQNSite,
    AQEReading,
    AQESite,
    SatelliteForecast,
    SatelliteBox,
)
from cleanair.models import ModelConfig, ModelData
from cleanair.types.dataset_types import DataConfig, FullDataConfig


@pytest.fixture(scope="class")
def model_config(secretfile, connection_class):

    return ModelConfig(secretfile=secretfile, connection=connection_class)


@pytest.fixture(scope="class")
def model_data(secretfile, connection_class):

    return ModelData(secretfile=secretfile, connection=connection_class)


@pytest.fixture()
def valid_full_config(valid_config, model_config):

    return model_config.generate_full_config(valid_config)


@pytest.fixture(scope="function")
def satellite_x_train() -> FeaturesDict:
    """Training dictionary."""
    return dict(laqn=np.random.rand(24, 3), satellite=np.random.rand(4, 5, 3),)


@pytest.fixture(scope="function")
def satellite_y_train() -> TargetDict:
    """Training target dict."""
    return dict(
        laqn=dict(NO2=np.random.rand(24, 1), PM10=np.random.rand(24, 1),),
        satellite=dict(NO2=np.random.rand(4, 1), PM10=np.random.rand(4, 1),),
    )
