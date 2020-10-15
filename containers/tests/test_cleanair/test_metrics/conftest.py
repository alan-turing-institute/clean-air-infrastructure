"""Fixtures for metrics."""

from datetime import datetime
from typing import List
from uuid import UUID
import pytest
import numpy as np
import pandas as pd
from nptyping import NDArray, Float64


# pylint: disable=redefined-outer-name

@pytest.fixture(scope="function")
def num_data_points() -> int:
    """Number of data points."""
    return 5

@pytest.fixture(scope="function")
def y_test() -> NDArray[Float64]:
    """Actual observations."""
    return np.array([0, 1, 5, 10, 100])


@pytest.fixture(scope="function")
def y_pred() -> NDArray[Float64]:
    """Predictions."""
    return np.array([0, 2, 10, 20, 0])

@pytest.fixture(scope="function")
def y_var(num_data_points) -> NDArray[Float64]:
    """Predicted variance."""
    return np.ones(num_data_points)

@pytest.fixture(scope="function")
def point_id() -> UUID:
    """A random point id."""
    return UUID()

@pytest.fixture(scope="function")
def timestamps(dataset_start_date: datetime, num_data_points) -> List:
    """List of timestamps for each data point."""
    return pd.date_range(start=dataset_start_date, freq="H", periods=num_data_points)

@pytest.fixture(scope="function")
def result_df(
    point_id: UUID, timestamps: List, y_pred: NDArray[Float64], y_var: NDArray[Float64]
) -> pd.DataFrame:
    """A dataframe of predictions for the mean and variance."""
    dframe = pd.DataFrame()
    dframe["measurement_start_utc"] = timestamps
    dframe["point_id"] = point_id
    dframe["NO2_mean"] = y_pred
    dframe["NO2_var"] = y_var
    return dframe

@pytest.fixture(scope="function")
def observation_df(point_id: UUID, timestamps: List, y_test: NDArray[Float64]) -> None:
    """Observations."""
    dframe = pd.DataFrame()
    dframe["measurement_start_utc"] = timestamps
    dframe["point_id"] = point_id
    dframe["NO2"] = y_test
    return dframe
