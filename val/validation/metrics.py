"""
Methods for evaluating metrics.
"""

import itertools
import pandas as pd
from sklearn import metrics

def evaluate_experiment(xp, metric_methods, evaluate_testing=True, evaluate_training=False):
    """
    Given an experiment, measure the metrics.
    
    We assume that the `model_data_list` of an experiment
    has already been updated with the predictions.

    Parameters
    ___

    xp : Experiment

    evaluate_testing : bool, optional
        If true, this function will evaluate the predictions made
        on the testing set of data.    

    evaluate_training : bool, optional
        If true, this function will evaluate the predictions made
        on the training set of data.

    Returns
    ___

    sensor_scores_df : pd.DataFrame
        For every instance of the experiment, we calculate the score
        of a sensor over the whole prediction time period.

    temporal_scores_df : pd.DataFrame
        For every instance of an experiment, we calculate the scores
        over all sensors given a slice in time.

    Notes
    ___

    We assume that all instances of an experiment predict on the same
    species of pollutant.

    Examples
    ___
        >>> xp.update_model_data_list() # remember to update predictions
        >>> scores_df = evaluate_experiment(xp)
    """
    # the basic cols that every scoring dataframe should have
    cols = [
        'experiment_name', 'instance_id' 'cluster_name', 'param_id',
        'data_id', 'training_set', 'testing_set'
    ]
    sensor_cols = cols.copy().append('point_id')
    temporal_cols = cols.copy().append('measurement_start_utc')

    # add columns that will measure the metrics for each pollutant
    list_of_species = xp.model_data_list[0].config['species'].copy()
    metric_cols = [
        '{species}_{mtc}'.format(species=s, mtc=m)
        for s, m in itertools.product(list_of_species, metric_methods.keys())
    ]
    sensor_cols.extend(metric_cols)
    temporal_cols.extend(metric_cols)

    # create dataframes for collecting scores over space and time
    sensor_scores_df = pd.DataFrame(columns=sensor_cols)
    temporal_scores_df = pd.DataFrame(columns=temporal_cols)

    # sensor_scores_df = pd.DataFrame(columns=)
    for model_data in xp.model_data_list:
        for spc in model_data.config['species']:
            # for each pollutant, measure the r2, mae and mse
            pred_col = '{s}_mean'.format(s=spc)
            if evaluate_training:
                # evaluate training predictions of sensors over the whole training period
                training_sensor_scores_df = measure_scores_by_sensor(
                    model_data.normalised_training_data_df, metric_methods,
                    pred_col=pred_col, test_col=spc
                )
                # evaluate training predictions for each timestamp over all sensors
                training_temporal_scores_df = measure_scores_by_hour(
                    model_data.normalised_training_data_df, metric_methods,
                    pred_col=pred_col, test_col=spc
                )
                # ToDo: append the scores dataframes
                
            elif evaluate_testing:
                # evaluate testing predictions of sensors over the whole testing period
                testing_sensor_scores_df = measure_scores_by_sensor(
                    model_data.normalised_pred_data_df, metric_methods,
                    pred_col=pred_col, test_col=spc
                )
                # evaluate testing predictions for each timestamp over all sensors
                testing_temporal_scores_df = measure_scores_by_hour(
                    model_data.normalised_testing_data_df, metric_methods,
                    pred_col=pred_col, test_col=spc
                )
                # ToDo: append the scores dataframes

    return sensor_scores_df, temporal_scores_df

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

def measure_scores_by_hour(pred_df, metric_methods, datetime_col='measurement_start_utc', pred_col='NO2_mean', test_col='NO2'):
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
    # remove nans from rows
    pred_df = __remove_rows_with_nans(pred_df, pred_col=pred_col, test_col=test_col)

    # group by datetime
    gb = pred_df.groupby(datetime_col)

    # get a series for each metric for all sensors at each hour
    # concat each series into a dataframe
    return pd.concat([
        pd.Series(gb.apply(
            lambda x : method(x[test_col], x[pred_col])
        ), name='{species}_{metric}'.format(species=test_col, metric=key))
        for key, method in metric_methods.items()
    ], axis=1, names=metric_methods.keys())

def measure_scores_by_sensor(pred_df, metric_methods, sensor_col='point_id', pred_col='NO2_mean', test_col='NO2'):
    """
    Group the pred_df by sensor then measure scores on each sensor.
    """
    # remove nans from rows
    pred_df = __remove_rows_with_nans(pred_df, pred_col=pred_col, test_col=test_col)

    # group by sensor id
    gb = pred_df.groupby(sensor_col)

    return pd.concat([
        pd.Series(gb.apply(
            lambda x : method(x[test_col], x[pred_col])
        ), name=key)
        for key, method in metric_methods.items()
    ], axis=1, names=metric_methods.keys())

def concat_static_features_with_scores(scores_df, pred_df, static_features=['lat', 'lon']):
    """
    Concatenate the sensor scores dataframe with static features of the sensor.
    """
    point_df = pd.DataFrame(index=list(scores_df.index))
    for feature in static_features:
        feature_list = []
        for pid in point_df.index:
            value = pred_df[pred_df['point_id'] == pid].iloc[0][feature]
            feature_list.append(value)
        point_df[feature] = pd.Series(feature_list, index=point_df.index)
    return pd.concat([scores_df, point_df], axis=1, ignore_index=False)

def __remove_rows_with_nans(pred_df, pred_col='NO2_mean', test_col='NO2'):
    return pred_df.loc[pred_df[[pred_col, test_col]].dropna().index]
    