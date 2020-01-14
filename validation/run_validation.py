import sys
import os
import json
import logging
import argparse
import pathlib
import pandas as pd
import numpy as np

# validation modules
import spatial
import temporal
import choose_sensors
import experiment
import metrics

# requires cleanair
sys.path.append("../containers")
from cleanair.models import ModelData, SVGP_TF1
from cleanair.databases import DBReader
from cleanair.databases.tables import LAQNSite

logging.basicConfig()

def get_LAQN_sensor_info(secret_fp):

    db_reader = DBReader(secretfile=secret_fp)

    with db_reader.dbcnxn.open_session() as session:
        
        LAQN_table = session.query(LAQNSite)

        return pd.read_sql(LAQN_table.statement, LAQN_table.session.bind)

def run_svgp_experiment(exp):
    """
    Train and predict using an svgp.
    """
    model_name = exp.models[0]

    for index, row in exp.experiment_df.iterrows():
        # get configs
        model_config = exp.model_params[model_name][row['param_id']]

        # get data from saved numpy array
        x_train = np.load(exp.data_config[row['data_id']]['x_train_fp'])
        y_train = np.load(exp.data_config[row['data_id']]['y_train_fp'])
        x_test = np.load(exp.data_config[row['data_id']]['x_test_fp'])
        y_test = np.load(exp.data_config[row['data_id']]['y_test_fp'])

        # get shapes
        print()
        print("x train shape:", x_train.shape)
        print("y train shape:", y_train.shape)
        print("x test shape:", x_test.shape)
        print("y test shape:", y_test.shape)

        # reshape into list of data
        X = [x_train[:, None, :]]
        Y = [y_train]
        Xs = [x_test[:, None, :]]
        Ys = [y_test]

        print("Xs[0] shape:", Xs[0].shape)
        print("Ys[0] shape:", Ys[0].shape)

        # fit model
        mdl = SVGP_TF1()
        mdl.fit(X, Y, max_iter=model_config['max_iter'], model_params=model_config, save_model_state=False)

        # predict on testing set
        # Xs = Xs[0][:, 0, :]
        y_mean, y_var = mdl.predict(Xs)
        print("shape of y mean and y var:", y_mean.shape, y_var.shape)

        # concatenate and save to file
        y_pred = np.concatenate([y_mean, y_var], axis=1)
        print("shape of y_pred:", y_pred.shape)
        np.save(row['y_pred_fp'], y_pred)

def setup_experiment(exp, base_dir='../run_model/experiments/'):
    """
    Given an experiment create directories, data and files.
    """
    # create directories if they don't exist
    exp_dir = base_dir + exp.name + '/'
    pathlib.Path(base_dir).mkdir(exist_ok=True)
    pathlib.Path(exp_dir).mkdir(exist_ok=True)
    pathlib.Path(exp_dir + 'results').mkdir(exist_ok=True)
    pathlib.Path(exp_dir + 'data').mkdir(exist_ok=True)
    pathlib.Path(exp_dir + 'meta').mkdir(exist_ok=True)
    pathlib.Path(exp_dir + 'model').mkdir(exist_ok=True)

    # get sensor info
    secret_fp = "../terraform/.secrets/db_secrets.json"

    # store a list of ModelData objects to validate over
    model_data_list = []

    # create ModelData objects for each roll
    for index, row in exp.experiment_df.iterrows():
        data_id = row['data_id']
        data_config = exp.data_config[data_id]

        # If the numpy files do not exist locally
        if not numpy_files_exist(data_config):
            # make new directory for data
            data_dir_path = exp_dir + 'data/data{id}'.format(id=data_id)
            pathlib.Path(data_dir_path).mkdir(exist_ok=True)

            # Get the model data and append to list
            model_data = ModelData(config=data_config, secretfile=secret_fp)
            model_data_list.append(model_data)

            # save config status of the model data object to the data directory
            # model_data.save_config_state(data_dir_path)

            print("x train shape:", model_data.get_training_data_arrays()['X'].shape)
            print("y train shape:", model_data.get_training_data_arrays()['Y'].shape)
            print("x test shape:", model_data.get_pred_data_arrays(return_y=True)['X'].shape)
            print("y test shape:", model_data.get_pred_data_arrays(return_y=True)['Y'].shape)
            print()
            print("x test shape without return_y:", model_data.get_pred_data_arrays(return_y=True)['X'].shape)
            print()
            if model_data.get_training_data_arrays()['X'].shape[0] != model_data.get_training_data_arrays()['Y'].shape[0]:
                raise Exception("training X and Y not the same length")

            if model_data.get_pred_data_arrays(return_y=True)['X'].shape[0] != model_data.get_pred_data_arrays(return_y=True)['Y'].shape[0]:
                raise Exception("testing X and Y not the same length")

            # save normalised data to numpy arrays
            np.save(data_config['x_train_fp'], model_data.get_training_data_arrays()['X'])
            np.save(data_config['y_train_fp'], model_data.get_training_data_arrays()['Y'])
            np.save(data_config['x_test_fp'], model_data.get_pred_data_arrays(return_y=True)['X'])
            np.save(data_config['y_test_fp'], model_data.get_pred_data_arrays(return_y=True)['Y'])

    # save experiment dataframe to csv
    exp.experiment_df.to_csv(exp_dir + 'meta/experiment.csv')

    # save data and params configs to json
    with open(exp_dir + 'meta/data.json', 'w') as fp:
        json.dump(exp.data_config, fp, indent=4)

    with open(exp_dir + 'meta/model_params.json', 'w') as fp:
        json.dump(exp.model_params, fp, indent=4)

def numpy_files_exist(data_config):
    return (
        os.path.exists(data_config['x_train_fp'])
        and os.path.exists(data_config['y_train_fp'])
        and os.path.exists(data_config['x_test_fp'])
        and os.path.exists(data_config['y_test_fp'])
    )

if __name__ == "__main__":
    # command line arguments
    parser = argparse.ArgumentParser(description="Run validation")
    parser.add_argument('-s', '--setup', action='store_true', help='setup an experiment with parameters and data')
    parser.add_argument('-r', '--read', action='store_true', help='read an experiment from files')
    parser.add_argument('-l', '--local', action='store_true', help='train and predict a model on the local machine')
    parser.add_argument('-n', '--name', type=str, help='name of the experiment')
    parser.add_argument('-c', '--cluster', type=str, help='name of the cluster')
    parser.add_argument('-m', '--model', type=str, help='name of the model')
    args = parser.parse_args()
    
    # setup experiment
    if args.setup and args.model == 'svgp':
        exp = experiment.SVGPExperiment(args.name, args.cluster)
        setup_experiment(exp)
        
    # read experiment from files
    elif args.read:
        exp = experiment.experiment_from_dir(args.name, args.model, args.cluster)
        print(exp.experiment_df)
        model_data_list = experiment.get_model_data_list_from_experiment(exp)

        # get the scores for each result in the experiment
        for model_data in model_data_list:
            scores = metrics.measure_scores_by_hour(model_data.normalised_pred_data_df, metrics.get_metric_methods())
            print(scores)
            print()

    # run a local model instead of on the cluster
    elif args.local:
        exp = experiment.experiment_from_dir(args.name, args.cluster)
        run_svgp_experiment(exp)

    # no available options
    else:
        print("Must pass either -s [--setup] or -r [--read] with -n, -c and -m flags set.")
