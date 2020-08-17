"""Contains all functionality to create forecasts of SCOOT data using different
methods of timeseries analysis from `scanstat.timeseries`"""

import logging
import datetime

import pandas as pd
import numpy as np

from .timeseries import hw_forecast, gp_forecast


def forecast(
    processed_train: pd.DataFrame,
    processed_test: pd.DataFrame,
    train_start: datetime,
    train_upto: datetime,
    forecast_start: datetime,
    forecast_upto: datetime,
    model_name: str = "HW",
    detectors: list = None,
) -> pd.DataFrame:

    """Firstly produces a forecast using input training data. Secondly, produces a dataframe containing
    actual counts (test data) and baseline predictions for each detectors at each time step.

    Args:
        proc_df: Dataframe of processed SCOOT data.
        train_start: Timestamp of beginning of training period
        train_upto: Timestamp of end of training period
        forecast_start: Timestamp of beginning of forecast period
        forecast_upto: Timestamp of end of forecast_period
        model_name: Forecast method to use for baseline, default is "HW" for Holt-Winters.
                Options: "HW", ("GP", "LSTM")
        detectors: List of detectors to look produce forecasts for. Default behaviour
                   produces forecasts for all detectors present in input dataframe.

    Returns:
        forecast_proc_df: Dataframe of SCOOT vehicle counts and baseline estimates
    """

    # Drop useless columns
    if not set(["rolling_threshold", "global_threshold"]) <= set(
        processed_train.columns
    ):
        raise KeyError("Train dataframe does not contain the correct columns")
    if not set(["rolling_threshold", "global_threshold"]) <= set(
        processed_test.columns
    ):
        raise KeyError("Test dataframe does not contain the correct columns")
    processed_train = processed_train.drop(
        ["rolling_threshold", "global_threshold"], axis=1
    )
    processed_test = processed_test.drop(
        ["rolling_threshold", "global_threshold"], axis=1
    )

    if not detectors:
        detectors = processed_train["detector_id"].drop_duplicates().to_numpy()

    logging.info(
        "Using data from %s to %s, to build %s forecasting model",
        train_start,
        train_upto,
        model_name,
    )
    logging.info(
        "Forecasting counts between %s and %s for %d detectors.",
        forecast_start,
        forecast_upto,
        len(detectors),
    )

    # Select forecasting model_name
    if model_name == "HW":
        y = hw_forecast(
            processed_train,
            train_start,
            train_upto,
            forecast_start,
            forecast_upto,
            detectors=detectors,
        )

    if model_name == "GP":
        y = gp_forecast(
            processed_train,
            train_start,
            train_upto,
            forecast_start,
            forecast_upto,
            detectors=detectors,
        )

    logging.info("Forecasting complete.")

    # Merge dataframe with actual counts with forecasted counts
    forecast_df = y.merge(
        processed_test,
        on=[
            "detector_id",
            "point_id",
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
