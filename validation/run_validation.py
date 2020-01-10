import sys
import os
import json
import logging
import argparse
import pandas as pd
import numpy as np

# validation modules
import spatial
import temporal
import choose_sensors
import experiment
import parameters
import metrics

# requires cleanair
sys.path.append("../containers")
from cleanair.models import ModelData
from cleanair.databases import DBReader
from cleanair.databases.tables import LAQNSite

logging.basicConfig()

def get_LAQN_sensor_info(secret_fp):

    db_reader = DBReader(secretfile=secret_fp)

    with db_reader.dbcnxn.open_session() as session:
        
        LAQN_table = session.query(LAQNSite)

        return pd.read_sql(LAQN_table.statement, LAQN_table.session.bind)

def default_setup_validation():
    """
    Get default parameters.
    Get default time range.
    Get processed data for time range.
    Save data to files.
    """
    # get parameters
    params_dict = parameters.create_svgp_params_dict()

    # create dates for rolling over
    train_start = "2019-11-01T00:00:00"
    train_n_hours = 48
    pred_n_hours = 24
    n_rolls = 1
    rolls = temporal.create_rolls(train_start, train_n_hours, pred_n_hours, n_rolls)
    data_dict = experiment.create_data_dict(rolls)

    # get sensor info
    secret_fp = "../terraform/.secrets/db_secrets.json"
    sensor_info_df = get_LAQN_sensor_info(secret_fp)
    sdf = choose_sensors.remove_closed_sensors(sensor_info_df, closure_date=train_start)
    sensors = list(sdf["point_id"])

    # get experiment dataframe
    experiment_df = experiment.create_experiments_df(
        data_id=data_dict.keys(), param_id=params_dict.keys()
    )

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
    model_data.update_model_results_df(pred_dict, y_pred, {
        'fit_start_time':data_config['pred_start_date']
    })

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
        y_var = np.random.normal(loc=2, scale=0.2, size=y_pred.shape)
        y_pred = np.concatenate([y_pred, y_var], axis=1)
        model_data = save_results(experiment_id, y_pred)
        scores = metrics.measure_scores_by_hour(model_data.normalised_pred_data_df, metrics.get_metric_methods())
        print(scores)
