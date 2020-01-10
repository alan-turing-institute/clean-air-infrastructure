# validation modules
import spatial
import temporal
import choose_sensors
import experiment
import parameters
import metrics

import sys
import os
import json
import logging
import pickle
import argparse
import datetime
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

# requires cleanair
sys.path.append("../containers")
from cleanair.models import ModelData, SVGP
from cleanair.loggers import get_log_level
from cleanair.databases import DBReader
from cleanair.databases.tables import LAQNSite

logging.basicConfig()

def get_LAQN_sensor_info(secret_fp):

    db_reader = DBReader(secretfile=secret_fp)

    with db_reader.dbcnxn.open_session() as session:
        
        LAQN_table = session.query(LAQNSite)

        return pd.read_sql(LAQN_table.statement, LAQN_table.session.bind)

def run_rolling(write_results=False, to_pickle=False, from_pickle=False):
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
        model_config = experiment.get_model_data_config_default(
            r['train_start_date'], r['train_end_date'],
            r['pred_start_date'], r['pred_end_date'],
            train_points=S, pred_points=S
        )

        # Get the model data and append to list
        model_data = ModelData(config=model_config, secretfile=secret_fp)
        model_data_list.append(model_data)

        # Write to pickle
        if to_pickle:
            pickle.dump(model_data, 'model_data/rolling_{train_start}.pickle'.format(train_start=r['train_start_date']))

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

def run_forecast(write_results=False, to_pickle=False, from_pickle=False):
    # Set dates for training and testing
    train_end = "2019-11-06T00:00:00"
    train_n_hours = 24
    pred_n_hours = 24
    pred_start = "2019-11-06T00:00:00"
    train_start = temporal.strtime_offset(train_end, -train_n_hours)
    pred_end = temporal.strtime_offset(pred_start, pred_n_hours)

    # get sensor data and select subset of sensors
    secret_fp = "../terraform/.secrets/db_secrets.json"
    sensor_info_df = get_LAQN_sensor_info(secret_fp)
    sdf = choose_sensors.remove_closed_sensors(sensor_info_df, closure_date=train_start)
    sensors = list(sdf["point_id"])
    
    # Model configuration
    model_config = experiment.get_model_config_default(
        train_start, train_end, pred_start, pred_end,
        train_points=sensors, pred_points=sensors
    )

    # Model fitting parameters
    model_params = get_model_params_default()

    # Get the model data
    if from_pickle:
        model_data = pickle.load(open('model_data/forecast.pickle', 'rb'))
    else:
        model_data = ModelData(config=model_config, secretfile=secret_fp)

    if to_pickle:
        pickle.dump(model_data, open('model_data/forecast.pickle', 'wb'))

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

def default_setup_validation():
    """
    Get default parameters.
    Get default time range.
    Get processed data for time range.
    Save data to files.
    """
    secret_fp = "../terraform/.secrets/db_secrets.json"
    params_dict = parameters.create_svgp_params_dict()
    print(params_dict)
    print()

    # create dates for rolling over
    train_start = "2019-11-01T00:00:00"
    train_n_hours = 48
    pred_n_hours = 24
    n_rolls = 1
    rolls = temporal.create_rolls(train_start, train_n_hours, pred_n_hours, n_rolls)
    data_dict = experiment.create_data_dict(rolls)
    print("Data dict:")
    print(data_dict)
    print()

    # get experiment dataframe
    experiment_df = experiment.create_experiments_df(
        data_id=data_dict.keys(), param_id=params_dict.keys()
    )
    print("Experiment")
    print(experiment_df)
    print()

    # store a list of ModelData objects to validate over
    model_data_list = []

    # create ModelData objects for each roll
    for index, row in experiment_df.iterrows():
        data_id = row['data_id']
        data_config = data_dict[data_id]

        # If the numpy files do not exist locally
        if not numpy_files_exist(data_config):
            # Get the model data and append to list
            model_data = ModelData(config=data_config, secretfile=secret_fp)
            model_data_list.append(model_data)

            # save data to numpy arrays
            np.save(data_config['x_train_fp'], model_data.get_training_data_arrays()['X'])
            np.save(data_config['y_train_fp'], model_data.get_training_data_arrays()['Y'])
            np.save(data_config['x_test_fp'], model_data.get_pred_data_arrays()['X'])
            np.save(data_config['y_test_fp'], model_data.get_pred_data_arrays(return_y=True)['Y'])

    # save experiment dataframe to csv
    experiment_df.to_csv('meta/experiment.csv')

    # save data and params configs to json
    with open('meta/data.json', 'w') as fp:
        json.dump(data_dict, fp, indent=4)

    with open('meta/svgp_params.json', 'w') as fp:
        json.dump(params_dict, fp, indent=4)

def numpy_files_exist(data_config):
    return (
        os.path.exists(data_config['x_train_fp'])
        and os.path.exists(data_config['y_train_fp'])
        and os.path.exists(data_config['x_test_fp'])
        and os.path.exists(data_config['y_test_fp'])
    )

def save_results(experiment_id, y_pred):
    """
    Take y_pred from the cluster, load model_data from files, 
    update model_data with the new prediction and return model_data.
    """
    # read csv of experiment
    experiment_df = pd.read_csv('meta/experiment.csv')

    # read json files for parameters and data
    with open('meta/svgp_params.json', 'r') as json_file:
        params_dict = json.load(json_file)
    with open('meta/data.json', 'r') as json_file:
        data_dict = json.load(json_file)

    # get info for experiment
    row = experiment_df.loc[experiment_id]
    data_id = row['data_id']
    data_config = data_dict[data_id]
    y_pred_fp = row['y_pred_fp']

    # save y_pred to numpy array
    np.save(y_pred_fp, y_pred)

    # load model_data object from local files and config
    model_data = load_model_data_from_files(data_config)

    pred_dict = model_data.get_pred_data_arrays(return_y=True)
    model_data.update_model_results_df(pred_dict, y_pred)

    return model_data

def load_model_data_from_files(model_data_config):
    secret_fp = "../terraform/.secrets/db_secrets.json"
    print(model_data_config)
    return ModelData(model_data_config, secretfile=secret_fp)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run validation")
    parser.add_argument('-s', '--setup', action='store_true', help='setup an experiment with parameters and data')
    parser.add_argument('-r', '--result', type=int, help='show results given an experiment id')
    args = parser.parse_args()
    
    if args.setup:
        default_setup_validation()
    else:
        experiment_id = args.result
        y_pred = np.load('data/data0_y_test.npy')
        model_data = save_results(experiment_id, y_pred)
        scores = metrics.measure_scores_by_hour(model_data.get_pred_data_arrays(return_y=True)['Y'], metrics.get_metric_methods())
        print(scores)
