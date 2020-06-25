"""Fixtures for the model data class."""

from typing import Any, Dict
import pytest
import uuid
import numpy as np
import pandas as pd
from sqlalchemy.engine import Connection
from cleanair.models import ModelData
from cleanair.types import DataConfig, FeaturesDict, TargetDict


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


@pytest.fixture(scope="function")
def training_df() -> pd.DataFrame:
    """Simple dataframe of training data."""
    timerange = pd.date_range("2020-01-01", "2020-01-02", freq="H", closed="left")
    point_id = uuid.uuid4()
    lat = np.random.rand()
    lon = np.random.rand()
    assert len(timerange) == 24
    data_df = pd.DataFrame(
        dict(measurement_start_utc=timerange, NO2=np.random.rand(24),)
    )
    data_df["epoch"] = data_df["measurement_start_utc"].apply(lambda x: x.timestamp())
    data_df["point_id"] = point_id
    data_df["source"] = "laqn"
    data_df["lat"] = lat
    data_df["lon"] = lon
    return data_df


class MockModelData:
    def __init__(self, training_df):
        self.training_df = training_df

    def mock_validate_config(self, config) -> bool:
        return True

    def mock_generate_full_config(self, config) -> DataConfig:
        config["x_names"] = ["epoch", "lat", "lon"] + config["features"]
        return config

    def mock_get_training_data_inputs(self) -> pd.DataFrame:
        return self.training_df

    def mock_get_pred_data_inputs(self) -> pd.DataFrame:
        return self.training_df


@pytest.fixture(scope="function")
def model_data(
    monkeypatch: Any,
    secretfile: str,
    connection: Connection,
    no_features_data_config: DataConfig,
    training_df: pd.DataFrame,
) -> ModelData:
    """Get a simple model data class that has mocked data."""
    # create a mocked model data object
    mock = MockModelData(training_df)

    # for private methods you must specify _ModelData first
    monkeypatch.setattr(
        ModelData, "_ModelData__validate_config", mock.mock_validate_config
    )
    monkeypatch.setattr(
        ModelData, "_ModelData__generate_full_config", mock.mock_generate_full_config
    )
    monkeypatch.setattr(
        ModelData, "get_training_data_inputs", mock.mock_get_training_data_inputs
    )
    monkeypatch.setattr(
        ModelData, "get_pred_data_inputs", mock.mock_get_pred_data_inputs
    )
    dataset = ModelData(
        no_features_data_config, secretfile=secretfile, connection=connection
    )
    print(dataset.normalised_training_data_df.head())
    return dataset
