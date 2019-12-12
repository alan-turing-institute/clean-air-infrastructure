import sys
import logging
import datetime
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
import pandas as pd 
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

def forecast(model_fitter, model_data):
    """
    Forecast air quality.
    """
    training_data_dict = model_data.get_training_data_arrays(dropna=True)
    predict_data_dict = model_data.get_test_data_arrays(dropna=False)

    model_fitter.fit(training_data_dict['X'],
                    training_data_dict['Y'],
                    max_iter=5,
                    model_params=model_params)

def rolling_forecast():
    """
    Train and predict for multiple time periods in a row.
    """
    pass

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

    # training_data_dict = model_data.training_data_df
    training_data_dict = model_data.get_training_data_arrays(dropna=True)
    predict_data_dict = model_data.get_pred_data_arrays(dropna=False, return_y=True)

    # Fit the model
    model_fitter = SVGP()

    print("X train shape:", training_data_dict["X"].shape)
    print("y train shape:", training_data_dict["Y"].shape)

    model_fitter.fit(training_data_dict['X'],
                     training_data_dict['Y'],
                     max_iter=5,
                     model_params=model_params,
                     refresh=1)

    # Get info about the model fit
    model_fit_info = model_fitter.fit_info()

    # Do prediction and write to database
    print("X predict shape:", predict_data_dict["X"].shape)
    Y_pred = model_fitter.predict(predict_data_dict['X'])

    print("Y predict shape:", Y_pred.shape)

    # Write the model results to the database
    model_data.update_model_results_df(
        predict_data_dict=predict_data_dict,
        Y_pred=Y_pred,
        model_fit_info=model_fit_info
    )

    print(model_data.normalised_pred_data_df[["predict_mean", "predict_var"]])
