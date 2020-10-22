"""Fixtures for metrics."""

from datetime import datetime
from typing import List
from uuid import uuid4, UUID
import pytest
import numpy as np
import pandas as pd
from nptyping import NDArray, Float64
from cleanair.metrics import AirQualityMetrics
from cleanair.types import Source, Species

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="class")
def point_ids(fake_laqn_svgp_instance) -> List[UUID]:
    """Get a list of point ids."""
    return fake_laqn_svgp_instance.data_config.train_interest_points[Source.laqn]

@pytest.fixture(scope="function")
def timestamps(dataset_start_date: datetime, dataset_end_date: datetime) -> List:
    """List of timestamps for each data point."""
    num_periods = (dataset_end_date - dataset_start_date).days * 24
    print(num_periods)
    return pd.date_range(start=dataset_start_date, freq="H", periods=num_periods)

@pytest.fixture(scope="function")
def num_training_data_points(point_ids, timestamps) -> int:
    """Number of data points."""
    return len(point_ids) * len(timestamps)

@pytest.fixture(scope="function")
def num_forecast_data_points(point_ids, num_forecast_days) -> int:
    """Number of data points in the forecast period."""
    return len(point_ids) * num_forecast_days * 24

@pytest.fixture(scope="function")
def y_test() -> NDArray[Float64]:
    """Actual observations."""
    return np.array([0, 1, 5, 10, 100])


@pytest.fixture(scope="function")
def y_pred() -> NDArray[Float64]:
    """Predictions."""
    return np.array([0, 2, 10, 20, 0])


@pytest.fixture(scope="function")
def y_var() -> NDArray[Float64]:
    """Predicted variance."""
    return np.ones(5)

@pytest.fixture(scope="function")
def result_df(
    dataset_start_date: datetime,
    dataset_end_date: datetime,
    point_ids: List[UUID],
    timestamps: List,
    y_pred: NDArray[Float64],
    y_var: NDArray[Float64],
    fake_laqn_svgp_instance,
) -> pd.DataFrame:
    """A dataframe of predictions for the mean and variance."""
    dframe = pd.DataFrame()
    dframe["measurement_start_utc"] = timestamps
    dframe["point_id"] = point_ids
    dframe["NO2_mean"] = y_pred
    dframe["NO2_var"] = y_var
    dframe["forecast"] = dframe.measurement_start_utc.apply(lambda x: dataset_start_date <= x < dataset_end_date)
    dframe["source"] = Source.laqn
    dframe["pollutant"] = Species.NO2
    dframe["instance_id"] = fake_laqn_svgp_instance.instance_id
    dframe["data_id"] = fake_laqn_svgp_instance.data_id
    return dframe

@pytest.fixture(scope="function")
def observation_df(point_ids: List[UUID], timestamps: List, y_test: NDArray[Float64]) -> None:
    """Observations."""
    dframe = pd.DataFrame()
    dframe["measurement_start_utc"] = timestamps
    dframe["point_id"] = point_ids
    dframe["NO2"] = y_test
    return dframe


@pytest.fixture(scope="function")
def metrics_calculator(fake_laqn_svgp_instance, secretfile, connection_class):
    """Test the init function of the air quality metrics class."""
    return AirQualityMetrics(
        fake_laqn_svgp_instance.instance_id, secretfile=secretfile, connection=connection_class
    )
