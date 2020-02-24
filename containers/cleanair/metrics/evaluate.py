"""
Methods for evaluating a model data fit.
"""

# pylint: disable=W0640

import pandas as pd
from sklearn import metrics
from . import precision


def pop_kwarg(kwargs, key, default):
    """Pop the value of key if its in kwargs, else use the default value."""
    return default if key not in kwargs else kwargs.pop(key)


def evaluate_model_data(model_data, metric_methods, **kwargs):
    """
    Given a model data object, evaluate the predictions.

    Parameters
    ___

    model_data : ModelData
        A model data object with updated predictions.

    metric_methods : dict
        A dictionary where keys are the name of a metric and values
        are a function that takes two numpy arrays of the same shape.

    kwargs : dict
        See Other Parameters.

    Returns
    ___

    sensor_scores_df : pd.DataFrame
        For every instance of the experiment, we calculate the score
        of a sensor over the whole prediction time period.

    temporal_scores_df : pd.DataFrame
        For every instance of an experiment, we calculate the scores
        over all sensors given a slice in time.

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

    Raises
    ___

    ValueError
        If value of kwargs are not valid values.
    """
    precision_methods = pop_kwarg(kwargs, "precision_methods", dict())
    evaluate_training = pop_kwarg(kwargs, "evaluate_training", False)
    evaluate_testing = pop_kwarg(kwargs, "evaluate_testing", True)
    pred_cols = pop_kwarg(kwargs, "pred_cols", ["NO2_mean"])
    test_cols = pop_kwarg(kwargs, "test_cols", ["NO2"])
    var_cols = pop_kwarg(kwargs, "var_cols", ["NO2_var"])

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
    precision_methods = pop_kwarg(kwargs, "precision_methods", dict())
    pred_cols = pop_kwarg(kwargs, "pred_cols", ["NO2_mean"])
    test_cols = pop_kwarg(kwargs, "test_cols", ["NO2"])
    # measure scores by sensor and by hour
    sensor_scores_df = measure_scores_on_groupby(
        pred_df, metric_methods, sensor_col, precision_methods=precision_methods,pred_cols=pred_cols, test_cols=test_cols
    )
    temporal_scores_df = measure_scores_on_groupby(
        pred_df, metric_methods, temporal_col, precision_methods=precision_methods, pred_cols=pred_cols, test_cols=test_cols
    )

    # add lat and lon to sensor scores cols
    sensor_scores_df = concat_static_features(sensor_scores_df, pred_df)

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

def measure_scores_by_hour(
    pred_df, metric_methods, datetime_col="measurement_start_utc", **kwargs
):
    """
    Measure metric scores for each hour of prediction.

    Parameters
    ___

    pred_df : DataFrame
        Indexed by datetime. Must have a column of testing data and
        a column from the predicted air quality at the same points
        as the testing data.

    metric_methods : dict
        Keys are name of metric.
        Values are functions that take in two numpy/series and compute the score.

    datetime_col : str, optional
        Name of the datetime columns in the dataframe.

    Returns
    ___

    scores : DataFrame
        Indexed by datetime.
        Each column is a metric in metric_methods.

    Other Parameters
    ___

    pred_cols : list, optional
        Names of the column that are predictions.
        Length must match `test_cols`.

    test_cols : list, optional
        Names of columns in the dataframe that are the true observations.

    var_cols : list, optional
        Columns containing the variance of predictions.
        Default is ["NO2_var"]
    """
    precision_methods = pop_kwarg(kwargs, "precision_methods", dict())
    pred_cols = pop_kwarg(kwargs, "pred_cols", ["NO2_mean"])
    test_cols = pop_kwarg(kwargs, "test_cols", ["NO2"])
    var_cols = pop_kwarg(kwargs, "var_cols", ["NO2_var"])
    
    # remove nans from rows
    pred_df = __remove_rows_with_nans(pred_df, pred_cols=pred_cols, test_cols=test_cols)

    # group by datetime
    pred_gb = pred_df.groupby(datetime_col)

    if len(test_cols) > 1:
        raise NotImplementedError("Can only validate one pollutant.")

    # ToDo: implement precision metrics are make general with sensor methods.
    print("Precision metrics not implemented.")

    # get a series for each metric for all sensors at each hour
    # concat each series into a dataframe
    return pd.concat(
        [
            pd.Series(
                pred_gb.apply(lambda x: method(x[test_cols[0]], x[pred_cols[0]])),
                name="{species}_{metric}".format(species=test_cols[0], metric=key),
            )
            for key, method in metric_methods.items()
        ],
        axis=1,
    )


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
    precision_methods = pop_kwarg(kwargs, "precision_methods", dict())
    pred_cols = pop_kwarg(kwargs, "pred_cols", ["NO2_mean"])
    test_cols = pop_kwarg(kwargs, "test_cols", ["NO2"])
    var_cols = pop_kwarg(kwargs, "var_cols", ["NO2_var"])

    # remove nans from rows
    pred_df = __remove_rows_with_nans(pred_df, pred_cols=pred_cols, test_cols=test_cols)

    # group by col
    pred_gb = pred_df.groupby(groupby_col)

    list_of_series = []
    # get metrics for accuracy
    for key, meth in metric_methods.items():
        for i, pollutant in enumerate(test_cols):
            pred_col = pred_cols[i]
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


def concat_static_features(scores_df, pred_df, static_features=None):
    """
    Concatenate the sensor scores dataframe with static features of the sensor.
    """
    if static_features is None:
        static_features = ["lat", "lon"]
    point_df = pd.DataFrame(index=list(scores_df.index))
    for feature in static_features:
        feature_list = []
        for pid in point_df.index:
            value = pred_df[pred_df["point_id"] == pid].iloc[0][feature]
            feature_list.append(value)
        point_df[feature] = pd.Series(feature_list, index=point_df.index)
    return pd.concat([scores_df, point_df], axis=1, ignore_index=False)


def __remove_rows_with_nans(pred_df, **kwargs):
    """Remove rows with NaN as an observation."""
    pred_cols = pop_kwarg(kwargs, "pred_cols", ["NO2_mean"])
    test_cols = pop_kwarg(kwargs, "test_cols", ["NO2"])
    cols_to_check = pred_cols.copy()
    cols_to_check.extend(test_cols)
    return pred_df.loc[pred_df[cols_to_check].dropna().index]
