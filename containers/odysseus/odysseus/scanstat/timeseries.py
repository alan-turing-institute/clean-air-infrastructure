"""Module to contain implementations of various time-series methods to be used
within the scan statistic framework. Currently only contains the Holt-Winters
exponentially smoothed method."""

import datetime

# from datetime import timedelta
import logging

import numpy as np
import pandas as pd
import gpflow

from tensorflow.python.framework.errors import InvalidArgumentError
from sklearn.preprocessing import MinMaxScaler


def holt_winters(
    train_data: pd.DataFrame,
    forecast_start: datetime,
    forecast_upto: datetime,
    alpha: float = 0.03869791,
    beta: float = 0.0128993,
    gamma: float = 0.29348953,
    detectors: list = None,
    method: str = "stitch",
) -> pd.DataFrame:

    """Time series forecast using Holt-Winters method.

    Args:
        train_data: Dataframe of 'processed' SCOOT data
        forecast_start: Timestamp of beginning of forecast period
        forecast_upto: Timestamp of end of forecast_period
        alpha: Optimisation parameter
        beta: Optimisation parameter
        gamma: Optimisation parameter
        detectors: List of detectors to look at. Defaults to all.
        method: string refering the the method for handling long forecasts; "gap" or "stitch"

    Returns:
        Dataframe forecast in same format as SCOOT input dataframe, with baseline
        counts instead of actual counts.
    """

    # Check parameter values
    if not 0 <= alpha <= 1:
        raise ValueError("alpha parameter must be between 0 and 1")
    if not 0 <= beta <= 1:
        raise ValueError("beta parameter must be between 0 and 1")
    if not 0 <= gamma <= 1:
        raise ValueError("gamma parameter must be between 0 and 1")

    # Get default detectors
    if detectors is None:
        detectors = train_data["detector_id"].drop_duplicates().to_numpy()

    # Figure out how many data points to estimate
    num_forecast_hours = (forecast_upto - forecast_start).days * 24

    framelist = []
    for detector in detectors:
        # Notation as in Expectation-Based Scan Statistic paper
        smooth = 1
        trend = 1
        hod = np.ones(24)
        one_det = train_data[train_data["detector_id"] == detector]

        # Ensure values are sorted before entering loop
        one_det = one_det.sort_values(by=["measurement_end_utc"])

        gap_hours = int(
            (forecast_start - one_det["measurement_end_utc"].max())
            / np.timedelta64(1, "h")
        )

        # HW algorithm
        for i in range(0, len(one_det)):
            hour = i % 24
            count = one_det["n_vehicles_in_interval"].iloc[i]
            smooth_new = (alpha * (count / hod[hour])) + (1 - alpha) * (smooth + trend)
            trend = beta * (smooth_new - smooth) + (1 - beta) * trend
            hod[hour] = gamma * (count / smooth_new) + (1 - gamma) * hod[hour]
            smooth = smooth_new

        baseline = []
        endtime = []
        starttime = []

        i += 1

        # Now insert gap between training and forecasting periods, if the method is "stitch" then the gap will be
        # no greater than 24 hours, where the forecast starts at the next equivalent hour

        if method == "stitch":
            gap_hours = gap_hours % 24

        if gap_hours > 0:
            for k in range(i, gap_hours + i):
                hour = k % 24
                base = (smooth + trend) * hod[hour]

                smooth_new = (alpha * (base / hod[hour])) + (1 - alpha) * (
                    smooth + trend
                )
                trend = beta * (smooth_new - smooth) + (1 - beta) * trend
                hod[hour] = gamma * (base / smooth_new) + (1 - gamma) * hod[hour]
                smooth = smooth_new
            k += 1
        else:
            k = i

        # Now build the forecast
        for j in range(k, num_forecast_hours + k):

            start = forecast_start + np.timedelta64(j - k, "h")
            end = forecast_start + np.timedelta64(j - k + 1, "h")

            hour = j % 24
            base = (smooth + trend) * hod[hour]
            baseline.append(base)
            endtime.append(end)
            starttime.append(start)

            smooth_new = (alpha * (base / hod[hour])) + (1 - alpha) * (smooth + trend)
            trend = beta * (smooth_new - smooth) + (1 - beta) * trend
            hod[hour] = gamma * (base / smooth_new) + (1 - gamma) * hod[hour]
            smooth = smooth_new

        forecasts = pd.DataFrame(
            {
                "detector_id": detector,
                "lon": one_det[one_det["detector_id"] == detector]["lon"].iloc[0],
                "lat": one_det[one_det["detector_id"] == detector]["lat"].iloc[0],
                "measurement_start_utc": starttime,
                "measurement_end_utc": endtime,
                "baseline": baseline,
                # This is intentional - each forecast ouptuts upper, lower, normal
                # columns regardless of whether they are meaningful.
                # It is deemed that the majority of forecasts will have meaningful
                # upper and lower columns with HW being the exception to the rule.
                "baseline_upper": baseline,
                "baseline_lower": baseline,
                "standard_deviation": 0.0,
            }
        )
        framelist.append(forecasts)
    return pd.concat(framelist)


def gp_forecast(
    train_data: pd.DataFrame,
    forecast_start: datetime,
    forecast_upto: datetime,
    kern: gpflow.kernels = None,
    detectors: list = None,
    method: str = "gap",
) -> pd.DataFrame:

    """Forecast using Gaussian Processes
    Args:
        train_data: Dataframe of processed SCOOT data spanning the training period
        forecast_start: Timestamp of beginning of forecast period
        forecast_upto: Timestamp of end of forecast_period
        kern: Specify custom gfplow kernel for GPR
        detectors: List of detectors to look at
        method: string refering the the method for handling long forecasts; "gap" or "stitch"
    Returns:
        Dataframe forecast in same format as SCOOT input dataframe
    """

    # Get default detectors
    if detectors is None:
        detectors = train_data["detector_id"].drop_duplicates().to_numpy()

    # Figure out how many data points to estimate
    num_forecast_hours = int((forecast_upto - forecast_start) / np.timedelta64(1, "h"))

    framelist = []
    for detector in detectors:

        one_det = train_data[train_data["detector_id"] == detector]

        Y = one_det["n_vehicles_in_interval"].to_numpy().reshape(-1, 1)
        Y = Y.astype(float)
        X = np.arange(1, len(Y) + 1, dtype=float).reshape(-1, 1)

        scaler = MinMaxScaler(feature_range=(-1, 1))
        y = scaler.fit_transform(Y)

        if kern is None:

            kern_pd = gpflow.kernels.Periodic(gpflow.kernels.SquaredExponential())
            kern_pw = gpflow.kernels.Periodic(gpflow.kernels.SquaredExponential())
            kern_se = gpflow.kernels.SquaredExponential()
            kern_pd.period.assign(24.0)
            kern_pw.period.assign(168.0)

            k = kern_pd * kern_pw + kern_se
        else:
            k = kern

        model = gpflow.models.GPR(data=(X, y), kernel=k, mean_function=None)
        opt = gpflow.optimizers.Scipy()

        try:
            opt.minimize(
                model.training_loss,
                model.trainable_variables,
                options=dict(maxiter=500),
            )
        except InvalidArgumentError:
            logging.info(
                "%s: covariance matrix not invertible, moving on to next detector",
                detector,
            )
            del model
            continue

        if method == "gap":
            # print(type(one_det.min()))
            int_start = (
                forecast_start - one_det["measurement_end_utc"].min()
            ) / np.timedelta64(1, "h")
            int_start = int_start + 1
            int_end = num_forecast_hours + int_start

        if method == "stitch":
            int_start = (
                forecast_start - one_det["measurement_end_utc"].max()
            ) / np.timedelta64(1, "h")
            int_start = int_start % 168 + (len(one_det))
            int_end = num_forecast_hours + int_start

        ## generate test points for prediction
        prediction_range = np.linspace(int_start, int_end, num_forecast_hours).reshape(
            num_forecast_hours, 1
        )  # test points must be of shape (N, D)

        ## predict mean and variance of latent GP at test points
        mean, var = model.predict_f(prediction_range)

        # reverse min_max scaler
        test_predict = scaler.inverse_transform(mean)
        test_var = scaler.inverse_transform(var)

        forecast_period = pd.date_range(
            start=forecast_start, end=forecast_upto - np.timedelta64(1, "h"), freq="H",
        )

        # organise data into dataframe similar to the SCOOT outputs
        forecast_df = pd.DataFrame(
            {
                "detector_id": detector,
                "lon": train_data[train_data["detector_id"] == detector]["lon"].iloc[0],
                "lat": train_data[train_data["detector_id"] == detector]["lat"].iloc[0],
                "measurement_start_utc": forecast_period,
                "measurement_end_utc": forecast_period + np.timedelta64(1, "h"),
                "baseline": test_predict.flatten(),
                "baseline_upper": test_predict.flatten()
                + 3 * np.sqrt(test_var.flatten()),
                "baseline_lower": test_predict.flatten()
                - 3 * np.sqrt(test_var.flatten()),
                "standard_deviation": np.sqrt(test_var.flatten()),
            }
        )

        framelist.append(forecast_df)

        del model

    return pd.concat(framelist)
