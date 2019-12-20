import spatial
import temporal
import choose_sensors
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

def run_rolling(write_results=False):
    # create dates for rolling over
    train_start = "2019-11-01T00:00:00"
    train_n_hours = 48
    pred_n_hours = 24
    n_rolls = 5
    rolls = temporal.create_rolls(train_start, train_n_hours, pred_n_hours, n_rolls)

    # get sensor data and select subset of sensors
    secret_fp = "../terraform/.secrets/db_secrets.json"
    sensor_info_df = get_LAQN_sensor_info(secret_fp)
    sdf = choose_sensors.remove_closed_sensors(sensor_info_df, closure_date=train_start)
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
    scores_df, results_df = temporal.rolling_forecast('svgp', model_data_list, model_params=model_params, return_results=True)
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
    train_start = temporal.strtime_offset(train_end, -train_n_hours)
    pred_end = temporal.strtime_offset(pred_start, pred_n_hours)

    # get sensor data and select subset of sensors
    secret_fp = "../terraform/.secrets/db_secrets.json"
    sensor_info_df = get_LAQN_sensor_info(secret_fp)
    sdf = choose_sensors.remove_closed_sensors(sensor_info_df, closure_date=train_start)
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
    scores, results = temporal.forecast(model_fitter, model_data, model_params=model_params, return_results=write_results)
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
