import sys
import logging
import argparse
import datetime
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np
from sklearn import metrics
sys.path.append("../containers")

from cleanair.models import ModelData, SVGP
from cleanair.loggers import get_log_level
from cleanair.databases import DBReader
from cleanair.databases.tables import LAQNSite

def get_LAQN_sensor_info(secret_fp):

    db_reader = DBReader(secretfile=secret_fp)

    with db_reader.dbcnxn.open_session() as session:
        
        LAQN_table = session.query(LAQNSite)

        return pd.read_sql(LAQN_table.statement, LAQN_table.session.bind)

def filter_sensors(sdf, removed_closed=True, closure_date=None):
    """
    Remove sensors that have closed.
    
    Parameters
    ___

    sdf : DataFrame
        Sensor data.

    removed_closed : bool, optional
        If the date the sensor closed is less than `closure_date` then
        remove the sensor.

    closure_date : str, optional
        If `removed_closed` is true, then remove all sensors that closed before this date.

    Returns
    ___
    
    DataFrame
    """
    if closure_date is None:
        closure_date = datetime.datetime.now().strftime("YYYY-MM-DD HH:MM:SS")
    if removed_closed:
        sdf = sdf[(pd.isnull(sdf["date_closed"])) | (sdf["date_closed"] > closure_date)]
    return sdf

def strtime_offset(strtime, offset_hours):
    """Give an datetime as an iso string and an offset and return a new time"""

    return (isoparse(strtime) + relativedelta(hours=offset_hours)).isoformat()

def forecast(model_fitter, model_data, model_params={}, max_iter=1000, return_results=False):
    """
    Forecast air quality.

    Parameters
    ___

    model_fitter : SVGP
        Model fitter object.

    model_data : ModelData
        Initialised model data object.

    model_params : dict
        Model parameters and settings.

    max_iter : int
        ToDo

    Returns
    ___

    scores : DataFrame
        Contains the validation scores for each hour of the forecast.

    """

    # get training and testing data
    model_data.normalised_training_data_df.to_csv('results/normalised_df.csv')
    training_data_dict = model_data.get_training_data_arrays(dropna=True)
    predict_data_dict = model_data.get_pred_data_arrays(dropna=True, return_y=True)
    x_test, y_test = predict_data_dict['X'], predict_data_dict['Y']

    # fit the model
    model_fitter.fit(training_data_dict['X'],
                    training_data_dict['Y'],
                    max_iter=max_iter,
                    model_params=model_params)

    # Get info about the model fit
    model_fit_info = model_fitter.fit_info()

    # Do prediction
    print("X test shape:", x_test.shape)
    print("Y test shape:", y_test.shape)
    pred = model_fitter.predict(x_test)

    # Write the model results to dataframe
    model_data.update_model_results_df(
        predict_data_dict=predict_data_dict,
        Y_pred=pred,
        model_fit_info=model_fit_info
    )
    
    # filter out nans
    print()
    print("### columns:")
    print(list(model_data.normalised_pred_data_df.columns))
    useful_df = model_data.normalised_pred_data_df[[
        'measurement_start_utc', 'point_id', 'source', 'location',
        'lat', 'lon', 'fit_start_time', 'predict_mean', 'predict_var'
    ] + model_data.y_names]

    pred_data_df = model_data.normalised_pred_data_df.copy()[['measurement_start_utc', 'predict_mean'] + model_data.y_names].dropna()
    
    # calculate scores for each metric for each hour over all sensors
    metric_methods = get_metric_methods()
    scores = measure_scores_by_hour(pred_data_df, metric_methods)

    if return_results:
        return scores, useful_df
    return scores

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

def create_rolls(train_start, train_n_hours, pred_n_hours, num_rolls):
    """Create a list of dictionaries with train and pred dates rolled up."""
    start_of_roll = train_start
    rolls = []

    for i in range(num_rolls):

        train_end = strtime_offset(start_of_roll, train_n_hours)
        pred_start = strtime_offset(start_of_roll, train_n_hours)
        pred_end = strtime_offset(pred_start, pred_n_hours)
        rolls.append({
            'train_start_date': start_of_roll,
            'train_end_date': train_end,
            'pred_start_date': pred_start,
            'pred_end_date': pred_end
        })
        start_of_roll = strtime_offset(start_of_roll, pred_n_hours)
    
    return rolls

def rolling_forecast(model_name, model_data_list, model_params={}, max_iter=1000, return_results=False):
    """
    Train and predict for multiple time periods in a row.
    """
    models = {
        "svgp":SVGP
    }
    roll = 0
    for model_data in model_data_list:
        print()
        print("iteration", roll)
        model_fitter = models[model_name]()
        if return_results:
            scores_df, pred_df = forecast(model_fitter, model_data, model_params=model_params, max_iter=max_iter, return_results=True)
        else:
            scores_df = forecast(model_fitter, model_data, model_params=model_params, max_iter=max_iter)
        
        # update all_preds if return_results is true
        if roll == 0 and return_results:
            all_preds_df = pred_df.copy()
        elif roll > 0 and return_results:
            all_preds_df = all_preds_df.append(pred_df)

        # update the metric results df
        if roll == 0:
            results_df = scores_df.copy()
        else:
            results_df = results_df.append(scores_df)
        roll += 1

    if return_results:
        return results_df, all_preds_df
    return results_df

def measure(actual, predict, r2=True, mae=True, mse=True, **kwargs):
    """
    Given a prediction and actual data, return the validation metrics.

    By default the custom metrics provided are r2, mae and mse.

    You can provide custom metrics using kwargs.
    A kwarg is given for each metric.
    The name of the metric is the key.
    A function is passed a value of the kwarg.
    See examples for more info.

    actual : array-like, shape = (n_samples, [n_output_dims])
        The actual target at the query points.

    predict : array-like, shape = (n_samples, [n_output_dims])
        The predicted targets at the query points.



    Returns
    ___

    dict
        Dictionary containing the results of the validation methods.
        Key is the name of the metric and value is the metric score.

    Examples
    ___

    The line below will return a dataframe with a single column.

    >> df = measure(actual, pred, r2=metrics.r2)
    """
    metric_methods = {}

    # default metrics
    if r2:
        metric_methods["r2"] = metrics.r2_score
    if mse:
        metric_methods["mse"] = metrics.mean_squared_error
    if mae:
        metric_methods["mae"] = metrics.median_absolute_error



    # compute and return metrics
    scores = {}
    for key, method in metric_methods.items():
        try:
            scores[key] = method(actual, predict)
        except ValueError:
            scores[key] = np.nan
    return scores

def run_rolling(write_results=False):
    # create dates for rolling over
    train_start = "2019-11-01T00:00:00"
    train_n_hours = 48
    pred_n_hours = 24
    n_rolls = 5
    rolls = create_rolls(train_start, train_n_hours, pred_n_hours, n_rolls)

    # get sensor data and select subset of sensors
    secret_fp = "../terraform/.secrets/db_secrets.json"
    sensor_info_df = get_LAQN_sensor_info(secret_fp)
    sdf = filter_sensors(sensor_info_df, closure_date=train_start)
    S = list(sdf["point_id"])

    # Model fitting parameters
    model_params = get_model_params_default()

    # store a list of ModelData objects to validate over
    model_data_list = []

    # create ModelData objects for each roll
    for r in rolls:
        # Model configuration
        model_config = get_model_config_default(
            r['train_start_date'], r['train_end_date'],
            r['pred_start_date'], r['pred_end_date'],
            train_points=S, pred_points=S
        )

        # Get the model data and append to list
        model_data = ModelData(secretfile=secret_fp)
        model_data.initialise(config=model_config)
        model_data_list.append(model_data)

    # Run rolling forecast
    scores_df, results_df = rolling_forecast('svgp', model_data_list, model_params=model_params, return_results=True)
    print(scores_df)
    scores_df.to_csv('results/rolling.csv')
    if write_results:
        results_df.to_csv('results/rolling_preds.csv')

def get_model_params_default():
    return {
        'lengthscale': 0.1,
        'variance': 0.1,
        'minibatch_size': 100,
        'n_inducing_points': 500
    }

def get_model_config_default(train_start, train_end, pred_start, pred_end, train_points='all', pred_points='all'):
    return {
        'train_start_date': train_start,
        'train_end_date': train_end,
        'pred_start_date': pred_start,
        'pred_end_date': pred_end,
        'train_sources': ['laqn', 'aqe'],
        'pred_sources': ['laqn', 'aqe'],
        'train_interest_points': train_points,
        'pred_interest_points': pred_points,
        'species': ['NO2'],
        'features': 'all',
        'norm_by': 'laqn',
        'model_type': 'svgp',
        'tag': 'testing'
    }

def run_forecast(write_results=False):
    # Set dates for training and testing
    train_end = "2019-11-06T00:00:00"
    train_n_hours = 72 * 2
    pred_n_hours = 48
    pred_start = "2019-11-06T00:00:00"
    train_start = strtime_offset(train_end, -train_n_hours)
    pred_end = strtime_offset(pred_start, pred_n_hours)

    # get sensor data and select subset of sensors
    secret_fp = "../terraform/.secrets/db_secrets.json"
    sensor_info_df = get_LAQN_sensor_info(secret_fp)
    sdf = filter_sensors(sensor_info_df, closure_date=train_start)
    sensors = list(sdf["point_id"])
    
    # Model configuration
    model_config = get_model_config_default(
        train_start, train_end, pred_start, pred_end,
        train_points=sensors, pred_points=sensors
    )

    # Model fitting parameters
    model_params = get_model_params_default()

    # Get the model data
    model_data = ModelData(secretfile=secret_fp)
    model_data.initialise(config=model_config)

    # print(model_data.list_available_features())
    # print(model_data.list_available_sources())
    # print(model_data.sensor_data_status(train_start, train_end, source = 'laqn', species='NO2'))

    # Fit the model
    model_fitter = SVGP()

    # Run validation
    scores, results = forecast(model_fitter, model_data, model_params=model_params, return_results=write_results)
    print(scores)
    scores.to_csv('results/forecast.csv')
    if write_results:
        results.to_csv('results/forecast_preds.csv')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run validation")
    parser.add_argument('-r', '--rolling', action='store_true')
    parser.add_argument('-w', '--write',  action='store_true')
    args = parser.parse_args()
    kwargs = vars(args)
    roll = kwargs.pop('rolling')
    write_results = kwargs.pop('write')
    logging.basicConfig()
    if roll:
        run_rolling(write_results=write_results)
    else:
        run_forecast(write_results=write_results)
