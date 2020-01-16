import sys
import os
import json
import logging
import argparse
import pathlib
import pandas as pd
import numpy as np
import importlib

# validation modules
import spatial
import temporal
import choose_sensors
import experiment
import metrics
import laptop

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

def run_svgp_experiment(exp, experiment_dir='../run_model/experiments/'):
    """
    Train and predict using an svgp.
    """
    # load each model
    models = {}
    for model_name in exp.models:
        path_to_model = experiment_dir + exp.name + '/models/m_{name}.py'.format(name=model_name)
        models[model_name] = importlib.import_module(path_to_model)

    # secret file for database info
    secret_fp = "../terraform/.secrets/db_secrets.json"

    for index, row in exp.experiment_df.iterrows():
        # get configs
        model_name = row['model_name']
        model_config = exp.model_params[model_name][row['param_id']]
        data_config = exp.data_config[row['data_id']]

        # run the model given param and data configs
        models[model_name].main(data_config, model_config, row, experiment_root=experiment_dir + exp.name + '/')

"""
        # get model data object from directory
        data_dir = experiment_dir + exp.name + '/data/data' + str(row['data_id'])
        model_data = ModelData(config_dir=data_dir, secretfile=secret_fp)
        print("Model data x_train size:", model_data.get_training_data_arrays()['X'].shape)

        # get data from saved numpy array
        x_train = np.load(data_config['x_train_fp'])
        y_train = np.load(data_config['y_train_fp'])
        x_test = np.load(data_config['x_test_fp'])
        y_test = np.load(data_config['y_test_fp'])

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
        Xs = Xs[0][:, 0, :]
        print(Xs.shape)
        y_mean, y_var = mdl.predict(Xs)
        print("shape of y mean and y var:", y_mean.shape, y_var.shape)

        # concatenate and save to file
        y_pred = np.concatenate([y_mean, y_var], axis=1)
        print("shape of y_pred:", y_pred.shape)
        np.save(row['y_pred_fp'], y_pred)
"""

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
    parser.add_argument('-r', '--run', action='store_true', help='train and predict a model')
    parser.add_argument('-n', '--name', type=str, help='name of the experiment')
    parser.add_argument('-c', '--cluster', type=str, help='name of the cluster')
    parser.add_argument('-m', '--model', type=str, help='name of the model')
    args = parser.parse_args()
    
    # setup experiment to run on a laptop
    if args.setup and args.cluster == 'laptop':
        laptop_experiment = laptop.LaptopExperiment(args.name)
        laptop_experiment.setup()

    # setup experiment
    elif args.setup and args.model == 'svgp':
        svgp_experiment = experiment.SVGPExperiment(args.name, args.cluster)
        svgp_experiment.setup()

    # run a model with local data
    elif args.run and args.cluster == 'laptop':
        svgp_experiment = experiment.experiment_from_dir(args.name, args.cluster)
        run_svgp_experiment(svgp_experiment)

    # no available options
    else:
        print("Must pass either -s [--setup] or -r [--read] with -n, -c and -m flags set.")
