import pytest
import numpy as np
import pandas as pd
from datetime import datetime
from ..gpjax_models.data.normalise import (
    normalise,
    denormalise,
    space_norm,
    time_norm,
    normalise_datetime,
    normalise_location,
)


def test_normalise():
    # Test 1D array
    X = np.array([1, 2, 3, 4, 5])
    normalized = normalise(X, X)
    assert np.allclose(np.mean(normalized), 0)
    assert np.allclose(np.std(normalized), 1)

    # Test 2D array
    X_2d = np.array([[1, 2], [3, 4], [5, 6]])
    normalized_2d = normalise(X_2d, X_2d)
    assert np.allclose(np.mean(normalized_2d, axis=0), [0, 0])
    assert np.allclose(np.std(normalized_2d, axis=0), [1, 1])


def test_denormalise():
    original = np.array([1, 2, 3, 4, 5])
    normalized = normalise(original, original)
    denormalized = denormalise(normalized, original)
    assert np.allclose(original, denormalized)


def test_space_norm():
    # Create sample data with 3 columns (time, lat, lon)
    X = np.array([[0, 51.5, -0.1], [0, 51.6, -0.2], [0, 51.7, -0.3]])
    wrt_X = X.copy()

    lat_norm, lon_norm = space_norm(X, wrt_X)
    assert len(lat_norm) == len(X)
    assert len(lon_norm) == len(X)
    assert np.allclose(np.mean(lat_norm), 0)
    assert np.allclose(np.mean(lon_norm), 0)


def test_time_norm():
    times = np.array([0, 3600, 7200])  # times in seconds
    normalized = time_norm(times, times)
    expected = np.array([0, 1 / 24, 2 / 24])  # converted to days
    assert np.allclose(normalized, expected)


def test_normalise_datetime():
    # Create sample DataFrame
    dates = pd.date_range(start="2023-01-01", periods=24, freq="H")
    df = pd.DataFrame({"measurement_start_utc": dates})

    # Test hour normalization
    hour_df = normalise_datetime(df.copy(), wrt="hour")
    assert "time" in hour_df.columns
    assert "time_norm" in hour_df.columns
    assert hour_df["time"].max() <= 23

    # Test clipped hour normalization
    clipped_df = normalise_datetime(df.copy(), wrt="clipped_hour")
    assert clipped_df["time_norm"].min() >= -1
    assert clipped_df["time_norm"].max() <= 1

    # Test epoch normalization
    epoch_df = normalise_datetime(df.copy(), wrt="epoch")
    assert "time" in epoch_df.columns
    assert "time_norm" in epoch_df.columns

    # Test invalid wrt parameter
    with pytest.raises(ValueError):
        normalise_datetime(df, wrt="invalid")


def test_normalise_location():
    # Create sample DataFrame
    df = pd.DataFrame({"lon": [-0.1, -0.2, -0.3], "lat": [51.5, 51.6, 51.7]})

    normalized_df = normalise_location(df)

    assert "lon_norm" in normalized_df.columns
    assert "lat_norm" in normalized_df.columns
    assert np.allclose(np.mean(normalized_df["lon_norm"]), 0)
    assert np.allclose(np.mean(normalized_df["lat_norm"]), 0)
    assert np.allclose(np.std(normalized_df["lon_norm"]), 1)
    assert np.allclose(np.std(normalized_df["lat_norm"]), 1)
