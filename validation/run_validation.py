import sys
import logging
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

def forecast(model_fitter, model_data, model_params={}, max_iter=5):
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

    df : DataFrame
        Contains the validation scores for each hour of the forecast.

    """
    training_data_dict = model_data.get_training_data_arrays(dropna=True)
    predict_data_dict = model_data.get_pred_data_arrays(dropna=False, return_y=True)
    x_test, y_test = predict_data_dict['X'], predict_data_dict['Y']

    model_fitter.fit(training_data_dict['X'],
                    training_data_dict['Y'],
                    max_iter=max_iter,
                    model_params=model_params)

    # Get info about the model fit
    model_fit_info = model_fitter.fit_info()

    # Do prediction and write to database
    print("X test shape:", x_test.shape)
    print("Y test shape:", y_test.shape)
    y_pred = model_fitter.predict(x_test)

    # Write the model results to dataframe
    model_data.update_model_results_df(
        predict_data_dict=predict_data_dict,
        Y_pred=y_pred,
        model_fit_info=model_fit_info
    )

    y_var = np.array(model_data.normalised_pred_data_df["predict_var"])
    print("Y var shape:", y_var.shape)
    print("Y predict shape:", y_pred.shape)

    # measure metrics and evaluate performance
    metrics = measure(y_test, y_pred)
    print(metrics)

def rolling_forecast():
    """
    Train and predict for multiple time periods in a row.
    """
    pass

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

    r2 : bool, optional
        Whether to use the r2 score.

    mae : bool, optional
        Whether to use the mae score.

    mse : bool, optional
        Whether to use mean squared error.

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

    # custom metrics
    for key, method in kwargs.items():
        metric_methods[key] = method

    # compute and return metrics
    scores = {}
    for key, method in metric_methods.items():
        try:
            scores[key] = method(actual, predict)
        except ValueError:
            scores[key] = np.nan
    return scores

if __name__ == "__main__":

    logging.basicConfig()

    # Set dates for training and testing
    train_end = "2019-11-02T00:00:00"
    train_n_hours = 24
    pred_n_hours = 24
    pred_start = "2019-11-02T00:00:00"
    train_start = strtime_offset(train_end, -train_n_hours)
    pred_end = strtime_offset(pred_start, pred_n_hours)

    # get sensor data and select subset of sensors
    secret_fp = "../terraform/.secrets/db_secrets.json"
    sensor_info_df = get_LAQN_sensor_info(secret_fp)
    sdf = filter_sensors(sensor_info_df, closure_date=train_start)
    print()
    print("Sensor data frame after filtering:")
    print(sdf)
    S = list(sdf["point_id"])
    
    # Model configuration
    model_config = {'train_start_date': train_start,
                    'train_end_date': train_end,
                    'pred_start_date': pred_start,
                    'pred_end_date': pred_end,
                    'train_sources': ['laqn', 'aqe'],
                    'pred_sources': ['laqn', 'aqe'],
                    'train_interest_points': S,
                    'pred_interest_points': S,
                    'species': ['NO2'],
                    'features': ['value_1000_building_height'],
                    'norm_by': 'laqn',
                    'model_type': 'svgp',
                    'tag': 'testing'}

    # Model fitting parameters
    model_params = {'lengthscale': 0.1,
                    'variance': 0.1,
                    'minibatch_size': 100,
                    'n_inducing_points': 500}


    # Get the model data
    model_data = ModelData(secretfile=secret_fp)
    model_data.initialise(config=model_config)


    # print(model_data.list_available_features())
    # print(model_data.list_available_sources())

    # print(model_data.sensor_data_status(train_start, train_end, source = 'laqn', species='NO2'))


    # Fit the model
    model_fitter = SVGP()

    # Run validation
    forecast(model_fitter, model_data, model_params=model_params)

    # print("X train shape:", training_data_dict["X"].shape)
    # print("y train shape:", training_data_dict["Y"].shape)

    # model_fitter.fit(training_data_dict['X'],
    #                  training_data_dict['Y'],
    #                  max_iter=5,
    #                  model_params=model_params,
    #                  refresh=1)

    # # Get info about the model fit
    # model_fit_info = model_fitter.fit_info()

    # # Do prediction and write to database
    # print("X predict shape:", predict_data_dict["X"].shape)
    # Y_pred = model_fitter.predict(predict_data_dict['X'])

    # print("Y predict shape:", Y_pred.shape)

    # # Write the model results to the database
    # model_data.update_model_results_df(
    #     predict_data_dict=predict_data_dict,
    #     Y_pred=Y_pred,
    #     model_fit_info=model_fit_info
    # )

    # print(model_data.normalised_pred_data_df[["predict_mean", "predict_var"]])
