import numpy as np
import pandas as pd
import pytest
from ..setup_data import (
    clean_data,
    norm_X,
    normalise,
    time_norm,
    space_norm,
    get_X,
    get_Y,
    get_X_trf,
    process_sat_data,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "epoch": [1000, 2000, 3000],
            "lat": [51.5, 51.6, 51.7],
            "lon": [-0.1, -0.2, -0.3],
            "value_200_total_a_road_primary_length": [100, 200, 300],
            "NO2": [40.0, 35.0, 45.0],
            "traffic": [500, 600, 700],
        }
    )


@pytest.fixture
def sample_sat_df():
    return pd.DataFrame(
        {
            "epoch": [1000, 1000, 2000, 2000],
            "lat": [51.5, 51.6, 51.5, 51.6],
            "lon": [-0.1, -0.2, -0.1, -0.2],
            "value_200_total_a_road_primary_length": [100, 200, 300, 400],
            "NO2": [40.0, 40.0, 35.0, 35.0],
            "box_id": [1, 1, 2, 2],
        }
    )


def test_clean_data():
    x = np.array([[1, 2], [3, np.nan], [5, 6]])
    y = np.array([[1], [2], [np.nan]])
    x_clean, y_clean = clean_data(x, y)

    assert x_clean.shape == (1, 2)
    assert y_clean.shape == (1, 1)
    assert not np.any(np.isnan(x_clean))
    assert not np.any(np.isnan(y_clean))


def test_normalise():
    X = np.array([[1, 2], [3, 4], [5, 6]])
    wrt_X = np.array([[1, 2], [3, 4], [5, 6]])

    result = normalise(X, wrt_X)

    assert result.shape == X.shape
    assert np.allclose(np.mean(result, axis=0), [0, 0], atol=1e-10)
    assert np.allclose(np.std(result, axis=0), [1, 1], atol=1e-10)


def test_time_norm():
    X = np.array([3600, 7200, 10800])  # 1, 2, 3 hours in seconds
    wrt_X = np.array([0, 3600, 7200, 10800])

    result = time_norm(X, wrt_X)

    assert np.allclose(result, np.array([1 / 24, 2 / 24, 3 / 24]))


def test_space_norm():
    X = np.array([[1, 10], [2, 20], [3, 30]])
    wrt_X = np.array([[1, 10], [2, 20], [3, 30]])

    lat_norm, lon_norm = space_norm(X, wrt_X)

    assert lat_norm.shape == (3,)
    assert lon_norm.shape == (3,)


def test_get_X(sample_df):
    result = get_X(sample_df)

    assert result.shape == (3, 4)
    assert np.all(result[:, 0] == sample_df["epoch"].values)
    assert np.all(result[:, 1] == sample_df["lat"].values)


def test_get_X_trf(sample_df):
    result = get_X_trf(sample_df)

    assert result.shape == (3, 5)
    assert np.all(result[:, -1] == sample_df["traffic"].values)


def test_get_Y(sample_df):
    result = get_Y(sample_df)

    assert result.shape == (3, 1)
    assert np.all(result[:, 0] == sample_df["NO2"].values)


def test_process_sat_data(sample_sat_df):
    X_sat, Y_sat = process_sat_data(sample_sat_df)

    assert X_sat.shape == (2, 2, 4)  # 2 box_ids, 2 points per box, 4 features
    assert Y_sat.shape == (2,)  # 2 box_ids


def test_norm_X():
    X = np.array(
        [[3600, 51.5, -0.1, 100], [7200, 51.6, -0.2, 200], [10800, 51.7, -0.3, 300]]
    )
    wrt_X = X.copy()

    result = norm_X(X, wrt_X)

    assert result.shape == X.shape
    # First column (time) should be in days
    assert np.all(result[:, 0] < 1)
    # Other columns should be normalized
    assert np.allclose(np.mean(result[:, 1:], axis=0), 0, atol=1e-10)
    assert np.allclose(np.std(result[:, 1:], axis=0), 1, atol=1e-10)
