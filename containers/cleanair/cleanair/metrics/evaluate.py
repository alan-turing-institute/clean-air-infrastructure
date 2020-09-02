"""
Methods for evaluating a model data fit.
"""

# pylint: disable=W0640

import pandas as pd
from sklearn import metrics
from . import precision


def evaluate_model_data(
    observation_df: pd.DataFrame, result_df: pd.DataFrame, metric_methods, **kwargs
):
    """
    Given a model data object, evaluate the predictions.

    Args:
        observation_df: Dataframe of the observed readings from sensors.
        result_df: Dataframe of predictions from a model.
        metric_methods: Keys are the name of a metric and values
            are a function that takes two numpy arrays of the same shape.

    Returns:
        sensor_scores_df: The score of a sensor over the whole prediction time period.
        temporal_scores_df : The scores over all sensors given a slice in time.

    Other Parameters
    ___

    precision_methods : dict, optional
        See `get_precision_methods()`.

    evaluate_testing : bool, optional
        If true, this function will evaluate the predictions made
        on the testing set of data.

    evaluate_training : bool, optional
        If true, this function will evaluate the predictions made
        on the training set of data.

    pred_cols : list, optional
        Columns containing predictions.
        Default is ["NO2_mean"].

    test_cols : list, optional
        Columns containing observations during prediction period.
        Default is ["NO2"].

    var_cols : list, optional
        Columns containing the variance of predictions.
        Default is ["NO2_var"]

    features : list, optional
        Names of columns that contain features we want to visualise.
        Default is ["lat", "lon"].

    Raises
    ___

    ValueError
        If value of kwargs are not valid values.
    """
    precision_methods = kwargs.pop("precision_methods", dict())
    evaluate_training = kwargs.pop("evaluate_training", False)
    evaluate_testing = kwargs.pop("evaluate_testing", True)
    pred_cols = kwargs.pop("pred_cols", ["NO2_mean"])
    test_cols = kwargs.pop("test_cols", ["NO2"])
    var_cols = kwargs.pop("var_cols", ["NO2_var"])

    if len(pred_cols) != len(test_cols):
        raise ValueError("pred_cols and test_cols must be the same length.")

    if evaluate_training:
        (
            training_sensor_scores_df,
            training_temporal_scores_df,
        ) = evaluate_spatio_temporal_scores(
            model_data.normalised_training_data_df,
            metric_methods,
            precision_methods=precision_methods,
            training_set=True,
            testing_set=False,
            pred_cols=pred_cols,
            test_cols=test_cols,
            var_cols=var_cols,
            **kwargs,
        )
        # return training scores if we are not evaluating testing
        if not evaluate_testing:
            return training_sensor_scores_df, training_temporal_scores_df

    if evaluate_testing:
        (
            testing_sensor_scores_df,
            testing_temporal_scores_df,
        ) = evaluate_spatio_temporal_scores(
            model_data.normalised_pred_data_df,
            metric_methods,
            precision_methods=precision_methods,
            training_set=False,
            testing_set=True,
            pred_cols=pred_cols,
            test_cols=test_cols,
            var_cols=var_cols,
            **kwargs,
        )
        # return testing scores if we are only evaluating testing
        if not evaluate_training:
            return testing_sensor_scores_df, testing_temporal_scores_df

    # return training and testing dataframes appending to eachother
    if evaluate_training and evaluate_testing:
        return (
            training_sensor_scores_df.append(
                testing_sensor_scores_df, ignore_index=True
            ),
            training_temporal_scores_df.append(
                testing_temporal_scores_df, ignore_index=True
            ),
        )
    raise ValueError(
        "You must set either evaluate_training or evaluate_testing to True"
    )


def evaluate_spatio_temporal_scores(
    pred_df,
    metric_methods,
    sensor_col="point_id",
    temporal_col="measurement_start_utc",
    **kwargs,
):
    """
    Given a prediction dataframe, measure scores over sensors and time.
    """
    # get keyword arguments
    precision_methods = kwargs.pop("precision_methods", dict())
    pred_cols = kwargs.pop("pred_cols", ["NO2_mean"])
    test_cols = kwargs.pop("test_cols", ["NO2"])
    var_cols = kwargs.pop("var_cols", ["NO2_var"])
    features = kwargs.pop("features", [])

    # measure scores by sensor and by hour
    sensor_scores_df = measure_scores_on_groupby(
        pred_df,
        metric_methods,
        sensor_col,
        precision_methods=precision_methods,
        pred_cols=pred_cols,
        test_cols=test_cols,
        var_cols=var_cols,
    )
    temporal_scores_df = measure_scores_on_groupby(
        pred_df,
        metric_methods,
        temporal_col,
        precision_methods=precision_methods,
        pred_cols=pred_cols,
        test_cols=test_cols,
        var_cols=var_cols,
    )

    # add lat and lon to sensor scores cols
    sensor_scores_df = concat_features(sensor_scores_df, pred_df, features)

    # make a new column with the index
    sensor_scores_df[sensor_col] = sensor_scores_df.index.copy()
    temporal_scores_df[temporal_col] = temporal_scores_df.index.copy()

    # meta info for the evaluation
    for key, value in kwargs.items():
        sensor_scores_df[key] = value
        temporal_scores_df[key] = value

    return sensor_scores_df, temporal_scores_df


def get_metric_methods(r2_score=True, mae=True, mse=True, **kwargs):
    """
    Get a dictionary of metric keys and methods.

    Parameters
    ___

    r2_score : bool, optional
        Whether to use the r2_score score.

    mae : bool, optional
        Whether to use the mae score.

    mse : bool, optional
        Whether to use mean squared error.

    kwargs : dict, optional
        Keys are names of metrics, values are a function that takes
        two numpy arrays of the same shape.

    Returns
    ___

    dict
        Key is a string of the metric name.
        Value is a metric evaluation function that takes
        two equally sized numpy arrays as parameters.
    """
    # measure each metric and store in metric_methods dictionary
    metric_methods = {}

    # default metrics
    if r2_score:
        metric_methods["r2_score"] = metrics.r2_score
    if mse:
        metric_methods["mse"] = metrics.mean_squared_error
    if mae:
        metric_methods["mae"] = metrics.median_absolute_error

    # custom metrics
    for key, method in kwargs.items():
        metric_methods[key] = method

    return metric_methods


def get_precision_methods(ci50=True, ci75=True, ci95=True, **kwargs):
    """
    Get a dictionary where the keys are the name of a metric and the values
    are a function that takes three arrays and computes the metric score.

    Parameters
    ___

    ci50 : bool, optional
        Calculate the confidence interval 50% score.

    ci75 : bool, optional
        Calculate the confidence interval 75% score.

    ci95 : bool, optional
        Calculate the confidence interval 95% score.

    kwargs : dict, optional
        More precision metrics.

    Returns
    ___

    precision_metrics : dict
        Get the keys and methods for the precision metrics.
    """
    # measure each metric and store in precision_methods dictionary
    precision_methods = {}

    # default metrics
    if ci95:
        precision_methods["ci95"] = precision.confidence_interval_95
    if ci75:
        precision_methods["ci75"] = precision.confidence_interval_75
    if ci50:
        precision_methods["ci50"] = precision.confidence_interval_50

    # custom metrics
    for key, method in kwargs.items():
        precision_methods[key] = method

    return precision_methods


def measure_scores_on_groupby(pred_df, metric_methods, groupby_col, **kwargs):
    """
    Group the pred_df then measure scores on each sensor.

    Parameters
    ___

    pred_df : DataFrame
        Contains predictions and observations.

    metric_methods : dict
        Keys are name of metric.
        Values are functions that take in two numpy/series and compute the score.

    groupby_col : str
        Name of the column containing the sensor ids.

    Returns
    ___

    pd.DataFrame
        Dataframe of scores by sensor.

    Other Parameters
    ___

    precision_methods : dict, optional
        Keys are the name of the metrics.
        Values are functions that take in three numpy/series and compute a precision score.

    pred_cols : list, optional
        Names of the column that are predictions.
        Length must match `test_cols`.

    test_cols : list, optional
        Names of columns in the dataframe that are the true observations.

    var_cols : list, optional
        Names of columns containing the variance of predictions.
    """
    precision_methods = kwargs.pop("precision_methods", dict())
    pred_cols = kwargs.pop("pred_cols", ["NO2_mean"])
    test_cols = kwargs.pop("test_cols", ["NO2"])
    var_cols = kwargs.pop("var_cols", ["NO2_var"])

    # remove nans from rows
    pred_df = __remove_rows_with_nans(pred_df, pred_cols=pred_cols, test_cols=test_cols)

    # group by col
    pred_gb = pred_df.groupby(groupby_col)

    list_of_series = []
    # get metrics for accuracy
    for key, meth in metric_methods.items():
        for i, pollutant in enumerate(test_cols):
            pred_col = pred_cols[i]
            # pylint: disable=undefined-loop-variable
            pollutant_metrics = pred_gb.apply(lambda x: meth(x[pollutant], x[pred_col]))
            pollutant_metrics_series = pd.Series(
                pollutant_metrics,
                name="{species}_{metric}".format(species=pollutant, metric=key),
            )
            list_of_series.append(pollutant_metrics_series)
    # get metrics for precision
    for key, meth in precision_methods.items():
        for i, pollutant in enumerate(test_cols):
            # get names of columns
            pred_col = pred_cols[i]
            var_col = var_cols[i]
            col_name = "{species}_{metric}".format(species=pollutant, metric=key)
            # run each precision metric
            pollutant_metrics = pred_gb.apply(
                lambda x: meth(x[pollutant], x[pred_col], x[var_col])
            )
            # add the metric to the list of scores
            pollutant_metrics_series = pd.Series(pollutant_metrics, name=col_name)
            list_of_series.append(pollutant_metrics_series)
    return pd.concat(list_of_series, axis=1)


def concat_features(scores_df, pred_df, features):
    """
    Concatenate the sensor scores dataframe with static features of the sensor.
    """
    point_df = pd.DataFrame(index=list(scores_df.index))
    pred_gb = pred_df.groupby("point_id")
    all_columns = features + ["lat", "lon"]
    for feature in all_columns:
        feature_list = []
        feature_name = feature
        for pid in point_df.index:
            # NOTE we could extend this to be any static feature, not just lat & lon
            if feature in ["lat", "lon"]:
                value = pred_df[pred_df["point_id"] == pid].iloc[0][feature]
            else:
                point_group = pred_gb.get_group(pid)
                value = point_group[feature].mean()
                feature_name = feature + "_mean"
            feature_list.append(value)
        point_df[feature_name] = pd.Series(feature_list, index=point_df.index)
    return pd.concat([scores_df, point_df], axis=1, ignore_index=False)


def __remove_rows_with_nans(pred_df, **kwargs):
    """Remove rows with NaN as an observation."""
    pred_cols = kwargs.pop("pred_cols", ["NO2_mean"])
    test_cols = kwargs.pop("test_cols", ["NO2"])
    cols_to_check = pred_cols.copy()
    cols_to_check.extend(test_cols)
    return pred_df.loc[pred_df[cols_to_check].dropna().index]
