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

    metric_methods : dict
        A dictionary where keys are the name of a metric and values
        are a function that takes two numpy arrays of the same shape.

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
        >>> metric_methods = get_metric_methods()
        >>> scores_df = evaluate_experiment(xp, metric_methods)
    """
    # the basic cols that every scoring dataframe should have
    cols = [
        'experiment_name', 'instance_id', 'cluster_name', 'param_id',
        'data_id', 'training_set', 'testing_set'
    ]
    sensor_cols = cols.copy()
    temporal_cols = cols.copy()
    sensor_cols.append('point_id')
    temporal_cols.append('measurement_start_utc')

    # add columns that will measure the metrics for each pollutant
    list_of_species = xp.model_data_list[0].config['species'].copy()
    print('List of species:', list_of_species)
    metric_cols = [
        '{species}_{mtc}'.format(species=s, mtc=m)
        for s, m in itertools.product(list_of_species, metric_methods.keys())
    ]
    print('Metric cols:', metric_cols)
    sensor_cols.extend(metric_cols)
    temporal_cols.extend(metric_cols)

    # create dataframes for collecting scores over space and time
    sensor_scores_df = pd.DataFrame(columns=sensor_cols)
    temporal_scores_df = pd.DataFrame(columns=temporal_cols)

    # sensor_scores_df = pd.DataFrame(columns=)
    for index, row in xp.experiment_df.iterrows():
        model_data = xp.model_data_list[index]

        # get prediction and testing column names
        pred_cols = ['{s}_mean'.format(s=spc) for spc in model_data.config['species']]
        test_cols = model_data.config['species'].copy()

        # evaluate the metrics at sensors and in time
        instance_sensor_scores_df, instance_temporal_scores_df = evaluate_model_data(
            model_data, metric_methods,
            evaluate_training=evaluate_training,
            evaluate_testing=evaluate_testing,
            pred_cols=pred_cols,
            test_cols=test_cols,
            experiment_name=xp.name,
            instance_id=index,
            cluster_name=xp.cluser_name,
            param_id=row['param_id'],
            data_id=row['data_id']
        )

        # append to the bigger dataframes
        sensor_scores_df = sensor_scores_df.append(instance_sensor_scores_df, ignore_index=True)
        temporal_scores_df = temporal_scores_df.append(instance_temporal_scores_df, ignore_index=True)

    return sensor_scores_df, temporal_scores_df

def evaluate_model_data(model_data, metric_methods, evaluate_training=False, evaluate_testing=True, pred_cols=['NO2_mean'], test_cols=['NO2'], **kwargs):
    """
    Given a model data object, evaluate the predictions.

    Parameters
    ___

    model_data : ModelData
        A model data object with updated predictions.

    metric_methods : dict
        A dictionary where keys are the name of a metric and values
        are a function that takes two numpy arrays of the same shape.

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
    """

    if evaluate_training:
        training_sensor_scores_df, training_temporal_scores_df = __evaluate_sensor_and_temporal_scores(
            model_data.normalised_training_data_df, metric_methods,
            training_set=True, testing_set=False,
            pred_cols=pred_cols, test_cols=test_cols, **kwargs
        )
        if not evaluate_testing:
            return training_sensor_scores_df, training_temporal_scores_df

    if evaluate_testing:
        testing_sensor_scores_df, testing_temporal_scores_df = __evaluate_sensor_and_temporal_scores(
            model_data.normalised_pred_data_df, metric_methods,
            training_set=False, testing_set=True,
            pred_cols=pred_cols, test_cols=test_cols, **kwargs
        )
        if not evaluate_training:
            return testing_sensor_scores_df, testing_temporal_scores_df

    if evaluate_training and evaluate_testing:
        return training_sensor_scores_df.append(testing_sensor_scores_df, ignore_index=True), training_temporal_scores_df.append(testing_temporal_scores_df, ignore_index=True)
    
    raise Exception("You must set either evaluate_training or evaluate_testing to True")

def __evaluate_sensor_and_temporal_scores(
            pred_df, metric_methods, pred_cols=['NO2_mean'], test_cols=['NO2'],
            sensor_col='point_id', temporal_col='measurement_start_utc', **kwargs
        ):
    """
    Given a prediction dataframe, measure scores over sensors and time.
    """
    sensor_scores_df = measure_scores_by_sensor(pred_df, metric_methods, pred_cols=pred_cols, test_cols=test_cols)
    temporal_scores_df = measure_scores_by_hour(pred_df, metric_methods, pred_cols=pred_cols, test_cols=test_cols)

    sensor_scores_df[sensor_col] = sensor_scores_df.index.copy()
    temporal_scores_df[temporal_col] = temporal_scores_df.index.copy()

    # meta info for the evaluation
    for key, value in kwargs.items():
        sensor_scores_df[key] = value
        temporal_scores_df[key] = value

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

def measure_scores_by_hour(pred_df, metric_methods, datetime_col='measurement_start_utc', pred_cols=['NO2_mean'], test_cols=['NO2']):
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

    pred_cols : list, optional
        Names of the column that are predictions.
        Length must match `test_cols`.

    test_cols : list, optional
        Names of columns in the dataframe that are the true observations.

    Returns
    ___

    scores : DataFrame
        Indexed by datetime.
        Each column is a metric in metric_methods.
    """
    # remove nans from rows
    pred_df = __remove_rows_with_nans(pred_df, pred_cols=pred_cols, test_cols=test_cols)

    # group by datetime
    gb = pred_df.groupby(datetime_col)

    # ToDo: generalise for multiple species

    # get a series for each metric for all sensors at each hour
    # concat each series into a dataframe
    return pd.concat([
        pd.Series(gb.apply(
            lambda x : method(x[test_cols[0]], x[pred_cols[0]])
        ), name='{species}_{metric}'.format(species=test_cols[0], metric=key))
        for key, method in metric_methods.items()
    ], axis=1)

def measure_scores_by_sensor(pred_df, metric_methods, sensor_col='point_id', pred_cols=['NO2_mean'], test_cols=['NO2']):
    """
    Group the pred_df by sensor then measure scores on each sensor.

    Parameters
    ___

    pred_df : DataFrame
        Indexed by datetime. Must have a column of testing data and
        a column from the predicted air quality at the same points 
        as the testing data.

    metric_methods : dict
        Keys are name of metric.
        Values are functions that take in two numpy/series and compute the score.

    sensor_col : str, optional
        Name of the column containing the sensor ids.
    
    pred_cols : list, optional
        Names of the column that are predictions.
        Length must match `test_cols`.

    test_cols : list, optional
        Names of columns in the dataframe that are the true observations.
    """
    # remove nans from rows
    pred_df = __remove_rows_with_nans(pred_df, pred_cols=pred_cols, test_cols=test_cols)

    # group by sensor id
    gb = pred_df.groupby(sensor_col)

    return pd.concat([
        pd.Series(gb.apply(
            lambda x : method(x[test_cols], x[pred_cols])
        ), name='{species}_{metric}'.format(species=test_cols[0], metric=key))
        for key, method in metric_methods.items()
    ], axis=1)

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

def __remove_rows_with_nans(pred_df, pred_cols=['NO2_mean'], test_cols=['NO2']):
    cols_to_check = pred_cols.copy()
    cols_to_check.extend(test_cols)
    return pred_df.loc[pred_df[cols_to_check].dropna().index]
    