"""Fixtures for metrics."""

from datetime import datetime
from typing import List
from uuid import UUID

import numpy as np
import pandas as pd
import pytest
from cleanair.experiment import AirQualityResult
from cleanair.metrics import AirQualityMetrics
from cleanair.types import Source, Species
import numpy.typing as npt


# pylint: disable=redefined-outer-name


@pytest.fixture(scope="class")
def point_ids(laqn_svgp_instance) -> List[UUID]:
    """Get a list of point ids."""
    return laqn_svgp_instance.data_config.train_interest_points[Source.laqn]


@pytest.fixture(scope="class")
def timestamps(dataset_start_date: datetime, dataset_end_date: datetime) -> List:
    """List of timestamps for each data point."""
    num_periods = (dataset_end_date - dataset_start_date).days * 24
    print(num_periods)
    return pd.date_range(start=dataset_start_date, freq="H", periods=num_periods)


@pytest.fixture(scope="class")
def num_training_data_points(point_ids, timestamps) -> int:
    """Number of data points."""
    return len(point_ids) * len(timestamps)


@pytest.fixture(scope="function")
def num_forecast_data_points(point_ids, num_forecast_days) -> int:
    """Number of data points in the forecast period."""
    return len(point_ids) * num_forecast_days * 24


@pytest.fixture(scope="function")
def y_test() -> npt.NDArray[np.float64]:
    """Actual observations."""
    return np.array([0, 1, 5, 10, 100])


@pytest.fixture(scope="function")
def y_pred() -> npt.NDArray[np.float64]:
    """Predictions."""
    return np.array([0, 2, 10, 20, 0])


@pytest.fixture(scope="function")
def y_var() -> npt.NDArray[np.float64]:
    """Predicted variance."""
    return np.ones(5)


@pytest.fixture(scope="function")
def observation_df(model_data, metrics_calculator):
    """Load and return the observations."""
    return metrics_calculator.load_observation_df(model_data)


@pytest.fixture(scope="class")
def result_df(
    num_training_data_points,
    point_ids: List[UUID],
    timestamps: List,
    laqn_svgp_instance,
) -> pd.DataFrame:
    """A dataframe of predictions for the mean and variance."""
    point_array = []
    timestamp_array = []
    for pid in point_ids:
        point_array.extend(np.repeat(str(pid), len(timestamps)).tolist())
        timestamp_array.extend(timestamps)
    dframe = pd.DataFrame()
    # dframe["measurement_start_utc"] = np.repeat(timestamps, len(point_ids))
    dframe["measurement_start_utc"] = timestamp_array
    print("len of time vs points:", len(dframe.measurement_start_utc), len(point_array))
    dframe["point_id"] = point_array
    dframe["NO2_mean"] = 2 * np.ones(num_training_data_points)
    dframe["NO2_var"] = np.ones(num_training_data_points)
    dframe["source"] = Source.laqn
    dframe["pollutant"] = Species.NO2
    dframe["instance_id"] = laqn_svgp_instance.instance_id
    dframe["data_id"] = laqn_svgp_instance.data_id
    return dframe


@pytest.fixture(scope="function")
def nans_df() -> pd.DataFrame:
    """Nans in some columns."""
    return pd.DataFrame(
        dict(
            NO2_mean=[1, 2, np.nan, 4],
            NO2_var=[1, 2, 3, np.nan],
            NO2=[1, np.nan, 3, 4],
            nan_column=[np.nan, np.nan, np.nan, np.nan],  # should be ignored in tests
        )
    )


@pytest.fixture(scope="function")
def metrics_calculator(laqn_svgp_instance, secretfile, connection_class):
    """Test the init function of the air quality metrics class."""
    laqn_svgp_instance.update_remote_tables()
    return AirQualityMetrics(
        laqn_svgp_instance.instance_id,
        secretfile=secretfile,
        connection=connection_class,
    )


@pytest.fixture(scope="class")
def svgp_result(secretfile, connection_class, result_df, laqn_svgp_instance):
    """Result fixture for svgp"""
    return AirQualityResult(
        laqn_svgp_instance.instance_id,
        laqn_svgp_instance.data_id,
        result_df=result_df,
        secretfile=secretfile,
        connection=connection_class,
    )
