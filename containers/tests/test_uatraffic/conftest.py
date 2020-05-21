"""Fixtures for uatraffic module."""

import pytest
import pandas as pd
import numpy as np


def generate_discrete_timeseries(
    size: int,
    lambda_noise: int = 5,
    constant_modifier: int = 50,
    amplitude_modifier: float = 10.0,
    shift_modifier: float = 3.0
):
    """Create a timeseries with discrete values."""
    X = np.linspace(0, size, num=size)

    # combine sine and cosine waves to create function
    underlying_function = constant_modifier + X + amplitude_modifier*(np.sin(0.5*X - shift_modifier) + np.cos(X))

    # floor function and add poisson noise
    return np.random.choice([-1, 1], size) * (np.random.poisson(lambda_noise, size) - 1) + np.floor(underlying_function)

@pytest.fixture(scope="function")
def scoot_df():
    """Fake dataframe of realistic scoot data."""
    columns = ["detector_id", "measurement_start_utc", "measurement_end_utc", "n_vehicles_in_interval"]
    frame = pd.DataFrame(columns=columns)

    start_time = "2020-01-01 00:00:00"
    end_time = "2020-01-02 23:00:00"
    detectors = ["A", "B"]
    date_range = pd.date_range(start=start_time, end=end_time, freq="h")
    size = len(date_range)

    for d in detectors:
        time_series = generate_discrete_timeseries(size)
        frame = pd.concat(
            [frame,
            pd.DataFrame.from_records(
                zip(
                    np.repeat(d, size),
                    date_range,
                    date_range + pd.DateOffset(hours=1),
                    time_series
                ),
                columns=columns,
            )],
            ignore_index=True,
        )
    return frame

@pytest.fixture(scope="function")
def anomalous_scoot_df(scoot_df):
    """Add some anomalies to the fake scoot data."""
    # get mean and standard deviation
    mean = scoot_df["n_vehicles_in_interval"].mean()
    std = scoot_df["n_vehicles_in_interval"].std()

    # add negative anomaly at index 6
    scoot_df.at[6, "n_vehicles_in_interval"] = -2

    # add zero anomaly at index 7
    scoot_df.at[7, "n_vehicles_in_interval"] = 0

    # add low anomaly at index 8 (this may also be negative)
    scoot_df.at[8, "n_vehicles_in_interval"] = mean - 3 * std - 1

    # add big anomaly at index 65
    scoot_df.at[65, "n_vehicles_in_interval"] = mean + 3 * std + 1

    return scoot_df
