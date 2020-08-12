"""Contains all functionality to create forecasts of SCOOT data using different
methods of timeseries analysis from `scanstat.timeseries`"""

import logging
import datetime

import pandas as pd
import numpy as np

from .timeseries import holt_winters, gp_forecast


def forecast(
    proc_df: pd.DataFrame,
    train_start: datetime,
    train_upto: datetime,
    forecast_start: datetime,
    forecast_upto: datetime,
    method: str = "HW",
    detectors: list = None,
) -> pd.DataFrame:

    """Produces a DataFrame where the count and baseline can be compared for use
        in scan statistics

    Args:
        proc_df: Dataframe of processed SCOOT data.
        train_start: Timestamp of beginning of training period
        train_upto: Timestamp of end of training period
        forecast_start: Timestamp of beginning of forecast period
        forecast_upto: Timestamp of end of forecast_period
        method: Forecast method to use for baseline, default is "HW" for Holt-Winters.
                Options: "HW", ("GP", "LSTM")
        detectors: List of detectors to look produce forecasts for. Default behaviour
                   produces forecasts for all detectors present in input dataframe.

    Returns:
        forecast_proc_df: Dataframe of SCOOT vehicle counts and baseline estimates
    """

    # Drop useless columns
    if not set(["rolling_threshold", "global_threshold"]) <= set(proc_df.columns):
        raise KeyError("Input dataframe does not contain the correct columns")
    proc_df = proc_df.drop(["rolling_threshold", "global_threshold"], axis=1)

    if not detectors:
        detectors = proc_df["detector_id"].drop_duplicates().to_numpy()

    train_data = proc_df[
        (proc_df["measurement_start_utc"] >= train_start)
        & (proc_df["measurement_end_utc"] <= train_upto)
    ]
    actual_counts = proc_df[
        (proc_df["measurement_start_utc"] >= forecast_start)
        & (proc_df["measurement_end_utc"] <= forecast_upto)
    ]

    logging.info(
        "Using data from %s to %s, to build %s forecasting model",
        train_start,
        train_upto,
        method,
    )
    logging.info(
        "Forecasting counts between %s and %s for %d detectors.",
        forecast_start,
        forecast_upto,
        len(detectors),
    )

    # Select forecasting method
    if method == "HW":
        y = holt_winters(train_data, forecast_start, forecast_upto, detectors=detectors)

    if method == "GP":
        y = gp_forecast(train_data, forecast_start, forecast_upto, detectors=detectors)

    logging.info("Forecasting complete.")

    # Merge actual_count dataframe with forecast dataframe, carry out checks
    # and return.
    forecast_df = y.merge(
        actual_counts,
        on=[
            "detector_id",
            "lon",
            "lat",
            "measurement_start_utc",
            "measurement_end_utc",
        ],
        how="left",
    )
    forecast_df.rename(
        columns={"n_vehicles_in_interval": "actual",}, inplace=True,
    )

    # Add check for NaNs cleanse
    actual_nans = forecast_df["actual"].isnull().sum(axis=0)
    baseline_nans = forecast_df["baseline"].isnull().sum(axis=0)
    if actual_nans != 0 or baseline_nans != 0:
        raise ValueError("Something went wrong with the forecast")

    # Make Baseline Values Non-Negative
    negative = len(forecast_df[forecast_df["baseline"] < 0]["baseline"])
    if negative > 0:
        logging.info("Setting %d negative baseline values to zero", negative)
        forecast_df["baseline"] = forecast_df["baseline"].apply(
            lambda x: np.max([0, x])
        )
        forecast_df["baseline_upper"] = forecast_df["baseline_upper"].apply(
            lambda x: np.max([0, x])
        )
    forecast_df["baseline_lower"] = forecast_df["baseline_lower"].apply(
        lambda x: np.max([0, x])
    )

    return forecast_df
