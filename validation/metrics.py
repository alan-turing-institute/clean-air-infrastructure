"""
Methods for evaluating metrics.
"""

import pandas as pd
from sklearn import metrics

def get_metric_methods(r2=True, mae=True, mse=True, **kwargs):
    """
    Get a dictionary of metric keys and methods.

    Parameters
    ___

    r2 : bool, optional
        Whether to use the r2 score.

    mae : bool, optional
        Whether to use the mae score.

    mse : bool, optional
        Whether to use mean squared error.

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
    if r2:
        metric_methods["r2"] = metrics.r2_score
    if mse:
        metric_methods["mse"] = metrics.mean_squared_error
    if mae:
        metric_methods["mae"] = metrics.median_absolute_error

    # custom metrics
    for key, method in kwargs.items():
        metric_methods[key] = method

    return metric_methods

def measure_scores_by_hour(pred_df, metric_methods, datetime_col='measurement_start_utc', pred_col='predict_mean', test_col='NO2'):
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

    Returns
    ___

    scores : DataFrame
        Indexed by datetime.
        Each column is a metric in metric_methods.
    """
    # group by datetime
    gb = pred_df.groupby(datetime_col)

    # get a series for each metric for all sensors at each hour
    # concat each series into a dataframe
    return pd.concat([
        pd.Series(gb.apply(
            lambda x : method(x[test_col], x[pred_col])
        ), name=key)
        for key, method in metric_methods.items()
    ], axis=1, names=metric_methods.keys())