"""Generating fake data for scoot."""

import string
import random
import numpy as np
import pandas as pd

def generate_discrete_timeseries(
    size: int,
    lambda_noise: int = 5,
    constant_modifier: int = 50,
    amplitude_modifier: float = 10.0,
    shift_modifier: float = 3.0,
    gradiant: float = 0.0,
) -> np.ndarray:
    """Create a timeseries with discrete values."""
    # set seed
    np.random.seed(0)

    X = np.linspace(0, size, num=size)

    # combine sine and cosine waves to create function
    underlying_function = constant_modifier + gradiant * X + amplitude_modifier*(np.sin(0.5*X - shift_modifier) + np.cos(X))

    # floor function and add poisson noise
    return np.random.choice([-1, 1], size) * (np.random.poisson(lambda_noise, size) - 1) + np.floor(underlying_function)

def generate_scoot_df(
    start_date: str = "2020-01-01",
    end_date: str = "2020-01-02",
    num_detectors: int = 1,
    day_of_week: int = 7,
) -> pd.DataFrame:
    """Generate a scoot dataframe.
    
    Args:
        start_date: First date.
        end_date: Last date (exclusive).
        num_detectors: Number of detectors to generate data for.
        day_of_week: 0 is Monday, 1 is Tuesday, etc.
            Default of 7 means all days are used.
    """
    # set seed
    random.seed(0)

    columns = ["detector_id", "measurement_start_utc", "measurement_end_utc", "n_vehicles_in_interval"]
    scoot_df = pd.DataFrame(columns=columns)

    for _ in range(num_detectors):
        # random detector id
        detector_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))

        # new dataframe with all dates between date range
        frame = pd.DataFrame()
        frame["measurement_start_utc"] = pd.date_range(start=start_date, end=end_date, freq="h", closed="left")
        num_observations = len(frame)

        # generate random discrete timeseries
        timeseries_center = random.randint(30, 3000)
        frame["n_vehicles_in_interval"] = generate_discrete_timeseries(
            num_observations,
            constant_modifier=timeseries_center,
            lambda_noise=int(timeseries_center / 10),
            amplitude_modifier=timeseries_center / 5,
        )
        # filter by day of week if applicable
        if day_of_week < 7:
            frame = frame.loc[frame["measurement_start_utc"].dayofweek() == day_of_week]
        
        frame["detector_id"] = detector_id
        frame["measurement_end_utc"] = frame["measurement_start_utc"] + pd.DateOffset(hours=1)

        # append new dataframe
        assert set(scoot_df.columns) == set(frame.columns)
        scoot_df = pd.concat([scoot_df, frame], ignore_index=True, sort=False)
    
    return scoot_df

def create_daily_readings_df(readings: np.ndarray) -> pd.DataFrame:
    """Create a simple dataframe over one day for one detector."""
    start_date = "2020-01-01"
    end_date = "2020-01-02"
    frame = pd.DataFrame()
    frame["n_vehicles_in_interval"] = readings
    frame["detector_id"] = np.repeat("A", 24)
    frame["measurement_start_utc"] = pd.date_range(start=start_date, end=end_date, freq="h", closed="left")
    frame["measurement_end_utc"] = frame["measurement_start_utc"] + pd.DateOffset(hours=1)
    return frame
