"""Module to contain implementations of various time-series methods to be used
within the scan statistic framework. Currently only contains the Holt-Winters
exponentially smoothed method."""

import datetime
from datetime import timedelta
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

        # Now build the forecast
        for j in range(num_forecast_hours):

            start = forecast_start + timedelta(hours=j)
            end = forecast_start + timedelta(hours=j + 1)

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
                "point_id": one_det[one_det["detector_id"] == detector][
                    "point_id"
                ].iloc[0],
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
) -> pd.DataFrame:

    """Forecast using Gaussian Processes
    Args:
        train_data: Dataframe of processed SCOOT data spanning the training period
        forecast_start: Timestamp of beginning of forecast period
        forecast_upto: Timestamp of end of forecast_period
        kern: Specify custom gfplow kernel for GPR
        detectors: List of detectors to look at
    Returns:
        Dataframe forecast in same format as SCOOT input dataframe
    """

    # Get default detectors
    if detectors is None:
        detectors = train_data["detector_id"].drop_duplicates().to_numpy()

    # Figure out how many data points to estimate
    num_forecast_hours = (forecast_upto - forecast_start).days * 24

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
            kern_w = gpflow.kernels.White()

            kern_pd.period.assign(24.0)
            kern_pw.period.assign(168.0)

            k = kern_pd * kern_pw + kern_se + kern_w
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

        ## generate test points for prediction
        prediction_range = np.linspace(
            len(Y) + 1, len(Y) + num_forecast_hours + 1, num_forecast_hours
        ).reshape(
            num_forecast_hours, 1
        )  # test points must be of shape (N, D)

        ## predict mean and variance of latent GP at test points
        mean, var = model.predict_f(prediction_range)

        # reverse min_max scaler
        test_predict = scaler.inverse_transform(mean)
        test_var = scaler.inverse_transform(var)

        forecast_period = pd.date_range(
            start=forecast_start, end=forecast_upto - timedelta(hours=1), freq="H",
        )

        # organise data into dataframe similar to the SCOOT outputs
        forecast_df = pd.DataFrame(
            {
                "detector_id": detector,
                "lon": train_data[train_data["detector_id"] == detector]["lon"].iloc[0],
                "lat": train_data[train_data["detector_id"] == detector]["lat"].iloc[0],
                "point_id": train_data[train_data["detector_id"] == detector][
                    "point_id"
                ].iloc[0],
                "measurement_start_utc": forecast_period,
                "measurement_end_utc": forecast_period + timedelta(hours=1),
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
