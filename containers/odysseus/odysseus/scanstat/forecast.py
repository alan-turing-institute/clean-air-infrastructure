"""Contains all functionality to create forecasts of SCOOT data using different
methods of timeseries analysis from `scanstat.timeseries`"""

import logging

import pandas as pd
import numpy as np

from .timeseries import holt_winters


def forecast(
    proc_df: pd.DataFrame,
    days_in_past: int,
    days_in_future: int,
    method: str = "HW",
    detectors: list = None,
    alpha: float = 0.1,
    beta: float = 0.1,
    gamma: float = 0.1,
    # kern=None,
) -> pd.DataFrame:

    """Produces a DataFrame where the count and baseline can be compared for use
        in scan statistics

    Args:
        proc_df: Dataframe of processed SCOOT data.
        days_in_past: Integer past days to train forecast on
        days_in_future: Days in future to produce a baseline estimate for
        method: Forecast method to use for baseline, default is "HW" for Holt-Winters.
                Options: "HW", ("GP", "LSTM")
        detectors: List of detectors to look produce forecasts for. Default behaviour
                   produces forecasts for all detectors present in input dataframe.
        alpha: Holt-Winter parameter
        beta: Holt-winters parameter
        gamma: Holt-winters parameter
        kern: (Inactive) GP kernel if method="GP" used. Default available.

    Returns:
        forecast_proc_df: Dataframe of SCOOT vehicle counts and baseline estimates
    """

    # Drop useless columns
    if not set(["rolling_threshold", "global_threshold"]) <= set(proc_df.columns):
        raise KeyError("Input dataframe does not contain the correct columns")
    proc_df = proc_df.drop(["rolling_threshold", "global_threshold"], axis=1)

    if days_in_future <= 0:
        raise ValueError("days_in_future must be a positive integer")
    if days_in_past <= 0:
        raise ValueError("days_in_past must be a positive integer")

    t_min = proc_df["measurement_start_utc"].min()
    t_max = proc_df["measurement_end_utc"].max()

    logging.info("Input dataframe contains data spanning %s to %s", t_min, t_max)

    if not detectors:
        detectors = proc_df["detector_id"].drop_duplicates().to_numpy()

    # Organise dates of train/forecast/analysis
    prediction_start = t_max - np.timedelta64(days_in_future * 24, "h")

    train_data = proc_df[proc_df["measurement_end_utc"] <= prediction_start]
    actual_counts = proc_df[proc_df["measurement_end_utc"] > prediction_start]

    avail_past_days = (prediction_start - t_min).days

    # Print sanity checks
    if avail_past_days < days_in_past:
        logging.info(
            "Input dataframe only contains %d days worth of data before the prediction period.",
            avail_past_days,
        )
        logging.info("Setting days_in_past = %d.", avail_past_days)
        forecast_data_start = t_min
    else:
        forecast_data_start = prediction_start - np.timedelta64(days_in_past, "D")

    logging.info(
        "Using data from %s to %s, to build %s forecasting model",
        forecast_data_start,
        prediction_start,
        method,
    )
    logging.info(
        "Forecasting counts between %s and %s for %d detectors.",
        prediction_start,
        t_max,
        len(detectors),
    )

    # Select forecasting method
    if method == "HW":
        y = holt_winters(
            train_data,
            days_in_past,
            days_in_future,
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            detectors=detectors,
        )

    #    if method == "LSTM":
    #       y = LSTM_forecast(
    #            df,
    #            days_in_past=days_in_past,
    #            days_in_future=days_in_future,
    #            detectors=detectors,
    #        )

    #    if method == "GP":
    #        y = GP_forecast(
    #            train_data,
    #            days_in_future=days_in_future,
    #            detectors=detectors,
    #            days_in_past=days_in_past,
    #            kern=kern,
    #        )

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
        columns={
            "n_vehicles_in_interval_x": "baseline",
            "n_vehicles_in_interval_y": "count",
        },
        inplace=True,
    )

    # Add check for NaNs cleanse
    count_nans = forecast_df["count"].isnull().sum(axis=0)
    baseline_nans = forecast_df["baseline"].isnull().sum(axis=0)
    assert count_nans == 0
    assert baseline_nans == 0

    # Make Baseline Values Non-Negative
    negative = len(forecast_df[forecast_df["baseline"] < 0]["baseline"])
    if negative > 0:
        logging.info("Setting %d negative baseline values to zero", negative)
        forecast_df["baseline"] = forecast_df["baseline"].apply(
            lambda x: np.max([0, x])
        )

    return forecast_df
