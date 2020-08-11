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
from cleanair.types.dataset_types import BaseConfig, FullConfig


@pytest.fixture(scope="class")
def model_config(secretfile, connection_class):

    return ModelConfig(secretfile=secretfile, connection=connection_class)


@pytest.fixture()
def valid_config(dataset_start_date, dataset_end_date):
    "Valid config for 'fake_cleanair_dataset' fixture"

    return BaseConfig(
        **{
            "train_start_date": dataset_start_date,
            "train_end_date": dataset_end_date,
            "pred_start_date": dataset_end_date,
            "pred_end_date": dataset_end_date + timedelta(days=2),
            "include_prediction_y": False,
            "train_sources": ["laqn", "aqe", "satellite"],
            "pred_sources": ["laqn", "aqe", "satellite", "hexgrid"],
            "train_interest_points": {"laqn": "all", "aqe": "all", "satellite": "all"},
            "pred_interest_points": {
                "laqn": "all",
                "aqe": "all",
                "satellite": "all",
                "hexgrid": "all",
            },
            "species": ["NO2"],
            "features": [
                "total_road_length",
                "total_a_road_length",
                "total_a_road_primary_length",
                "total_b_road_length",
                "grass",
                "building_height",
                "water",
                "park",
                "max_canyon_narrowest",
                "max_canyon_ratio",
            ],
            "buffer_sizes": ["1000", "500"],
            "norm_by": "laqn",
            "model_type": "svgp",
        }
    )


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
