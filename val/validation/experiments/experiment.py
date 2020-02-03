"""
The base class for experiments.
"""

import os
import sys
import json
import pickle
from abc import ABC, abstractmethod
import pandas as pd
import pathlib
import itertools

from .. import util
import os

from ..cluster import *

#requires cleanair
sys.path.append("../containers/")
sys.path.append("../../containers/")

try:
    from cleanair.models import ModelData
except ImportError:
    print('WARNING: Could not import ModelData')

class Experiment(ABC):
    def __init__(self, experiment_name, models, cluster_name, **kwargs):
        """
        An abstract experiment class.

        Parameters
        ___

        experiment_name : str
            Name that identifies the experiment.

        models : list
            List of string identifying the models to run in the experiment.

        cluster_name : str
            String to identify the cluster the experiment was ran on.

        model_params : list of dicts
            A list of model parameter configurations.
            Each model config is a dictionary.

        data_config : list of dicts
            A list of data configurations.
            Each config is a dictionary.

        experiment_df : DataFrame
            A dataframe describing every run in the experiment.
        """
        super().__init__()
        self.name = experiment_name
        self.models = models
        self.cluster = cluster_name
        self.model_params = kwargs['model_params'] if 'model_params' in kwargs else []
        self.data_config = kwargs['data_config'] if 'data_config' in kwargs else []
        self.experiment_df = kwargs['experiment_df'] if 'experiment_df' in kwargs else pd.DataFrame()
        self.model_data_list = kwargs['model_data_list'] if 'model_data_list' in kwargs else []
        self.directory = kwargs['directory'] if 'directory' in kwargs else 'experiment_data/'
        self.home_directory = kwargs['home_directory'] if 'home_directory' in kwargs else '~'
        self.secretfile = kwargs['secretfile'] if 'secretfile' in kwargs else '../terraform/.secrets/db_secrets.json'
        self.cluster_root = 'validation/cluster'

        self.directory = util.ensure_last_backslash(self.directory)
        self.home_directory = util.ensure_last_backslash(self.home_directory)

        self.available_clusters = {
            'laptop': Laptop,
            'pearl': Pearl,
            'orac': Orac
        }

    @abstractmethod
    def get_default_model_params(self):
        """
        Get the default parameters of the model for this experiment.
        """

    @abstractmethod
    def get_default_data_config(self):
        """
        Get the default data configurations for this experiment.
        """

    def get_default_experiment_df(self):
        """
        Create a dataframe where each line is one run/result of an experiment.
        """
        cols = ['model_name', 'param_id', 'data_id', 'cluster']
        experiment_df = pd.DataFrame(columns=cols)

        for model_name in self.models:
            # configs for this model
            experiment_configs = {
                'model_name':[model_name],
                'param_id':[item['id'] for item in self.model_params[model_name]],
                'data_id':[item['id'] for item in self.data_config],
                'cluster':[self.cluster]
            }
            list_of_configs = [values for key, values in experiment_configs.items()]
            params_configs = list(itertools.product(*list_of_configs))

            # append to experiments dataframe
            experiment_df = experiment_df.append(pd.DataFrame(params_configs, columns=cols), ignore_index=True)

        experiment_df['results_dir'] = pd.Series([
            util.create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) for r in experiment_df.itertuples()])

        experiment_df['model_state_fp'] = pd.Series([
            self.directory + '{name}/models/restore/m_{model_name}_'.format(name=self.name, model_name=r.model_name) + util.create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + '.model' for r in experiment_df.itertuples()])

        return experiment_df

    def setup(self, force_redownload=False):
        """
        Given an experiment create directories, data and files.
        """
        # create directories for experiment data
        experiment_dir = self.directory + self.name + '/'
        self.__create_experiment_data_directories()

        # store a list of ModelData objects to validate over
        self.model_data_list = []

        # create ModelData objects for each roll
        # Each roll is defined by data_id in experiment_df
        for data_id in pd.unique(self.experiment_df['data_id']):
            data_config = self.data_config[data_id]

            # If the numpy files do not exist locally
            if force_redownload or not util.pickle_files_exist(data_config):
                # make new directory for data
                data_dir_path = experiment_dir + 'data/data{id}'.format(id=data_id)
                pathlib.Path(data_dir_path).mkdir(exist_ok=True)

                # Get the model data and append to list
                model_data = ModelData(config=data_config, secretfile=self.secretfile)
                self.model_data_list.append(model_data)

                # save config status of the model data object to the data directory
                model_data.save_config_state(data_dir_path)

                # get the training and testing dicts indexed by source
                training_dict = model_data.get_training_dict()
                test_dict = model_data.get_test_dict()

                # write to a pickle
                with open(data_config['train_fp'], 'wb') as handle:
                    pickle.dump(training_dict, handle)
                with open(data_config['test_fp'], 'wb') as handle:
                    pickle.dump(test_dict, handle)

        # load and write model data objects to files
        self.save_meta_files()

    def save_meta_files(self):
        """
        Save the experiment_df, model_params and data_config to csv and json.
        """
        exp_dir = self.directory + self.name + '/'

        # save experiment dataframe to csv
        self.experiment_df.to_csv(exp_dir + 'meta/experiment.csv')

        # save data and params configs to json
        with open(exp_dir + 'meta/data.json', 'w') as fp:
            json.dump(self.data_config, fp, indent=4)

        with open(exp_dir + 'meta/model_params.json', 'w') as fp:
            json.dump(self.model_params, fp, indent=4)

    def __create_experiment_data_directories(self):
        """
        Create data directories if they don't exist.
        """
        exp_dir = self.directory + self.name + '/'
        pathlib.Path(self.directory).mkdir(exist_ok=True)
        pathlib.Path(exp_dir).mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'results').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'data').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'meta').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'models').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'models/restore').mkdir(exist_ok=True)

    def __create_experiment_results_directories(self):
        """
        Create directories to store results in if they don't already exist.
        """
        for row in self.experiment_df.itertuples():
            pathlib.Path(os.path.join(self.directory, self.name, 'results', row.results_dir)).mkdir(exist_ok=True)

    def __get_cluster_obj(self):
        """
        Load cluster object from cluster object and check it exists.
        """
        if self.cluster in self.available_clusters:
            return self.available_clusters[self.cluster]
        else:
            raise ValueError("Cluster does not exist: ",self.cluster)

    def get(self):
        """
        Get results from cluster.
        """
        experiment_df = self.get_default_experiment_df()
        cluster_run_params = []
        input_format_fn = lambda config: ' {param_id} {data_id}'.format(data_id=config['data_id'], param_id=config['param_id'])
        
        cluster = self.__get_cluster_obj()(
            root = 'validation/cluster/',
            experiment_name=self.name,
            cluster_config={},
            experiment_configs=cluster_run_params,
            input_format_fn=input_format_fn,
            cluster_tmp_fp=self.directory+'cluster',
            experiment_fp=self.directory,
            home_directory_fp=self.home_directory,
        )
        cluster.setup()

        cluster.get()

    def run(self):
        """
        Run the experiment.
        """
        # before running any models, create the results directories
        self.__create_experiment_results_directories()
        experiment_df = self.get_default_experiment_df()

        cluster_run_params = []

        for model in self.models:
            model_experiment_df = experiment_df[experiment_df['model_name'] == model]
            for index, row in model_experiment_df.iterrows():
                exp_dict = {
                    'filename': model,
                    'data_id': row['data_id'],
                    'param_id': row['param_id']
                }
                cluster_run_params.append(exp_dict)


        input_format_fn = lambda config: ' {param_id} {data_id}'.format(data_id=config['data_id'], param_id=config['param_id'])

        print(self.directory+'../libs/')

        cluster = self.__get_cluster_obj()(
            root = 'validation/cluster/',
            experiment_name=self.name,
            cluster_config={},
            experiment_configs=cluster_run_params,
            input_format_fn=input_format_fn,
            cluster_tmp_fp=self.directory+'cluster',
            experiment_fp=self.directory,
            home_directory_fp=self.home_directory,
            libs=['../containers/cleanair/'],
            relative_fp_flag=True
        )
        cluster.setup()
        return cluster


    def run(self):
        """
        Run the experiment.
        """
        # before running any models, create the results directories
        self.__create_experiment_results_directories()

        cluster = self.__get_cluster()

        #Ensure cluster folders exist
        dir_name = self.directory+'cluster'
        pathlib.Path(dir_name).mkdir(exist_ok=True)

        dir_name = self.directory+'cluster'+'/results/'
        pathlib.Path(dir_name).mkdir(exist_ok=True)

        for row in self.experiment_df.itertuples():

            dir_name = self.directory+'cluster'+'/results/'+os.path.basename(row.results_dir)
            pathlib.Path(dir_name).mkdir(exist_ok=True)


        cluster.run()

    def get(self):
        """
        Get the experiments results.
        """
        cluster = self.__get_cluster()

        cluster.get()


    def check_status(self):
        """
        Check the status of an experiment on a cluster.
        """
        cluster = self.__get_cluster()
        cluster.check()

    def clean(self):
        """
        Clean up after experiment. Remove tempory files locally and on cluster.
        """
        cluster = self.__get_cluster()
        cluster.clean()

    def update_model_data_list(self, update_test=True, update_train=False):
        """
        Update the model data list from local files.

        Parameters
        ___

        update_test : bool, optional
            The normalised_pred_data_df for each model data object is updated with new predictions.

        update_train : bool, optional
            The normalised_training_data_df for each model data object is updated with new predictions.
            There must exist a `train_pred.pickle` file in the results directory for each result.
        """
        model_data_list = []
        for index, row in self.experiment_df.iterrows():
            # load model data from directory
            config_dir = self.directory + '{name}/data/data{id}/'.format(name=self.name, id=row['data_id'])
            model_data = ModelData(config_dir=config_dir, secretfile=self.secretfile)

            # get the predictions from the model for testing data
            results_dir = row['results_dir']
            if update_test:
                test_pred_fp = '{dir}{name}/results/{id}/test_pred.pickle'.format(dir=self.directory, name=self.name, id=results_dir)
                with open(test_pred_fp, 'rb') as handle:
                    print()
                    print(test_pred_fp)
                    print()
                    test_pred_dict = pickle.load(handle)

                # update model data with predictions
                model_data.update_testing_df_with_preds(test_pred_dict)

            if update_train:
                # try to update the predictions for the training set
                try:
                    train_pred_fp = '{dir}{name}/results/{id}/train_pred.pickle'.format(dir=self.directory, name=self.name, id=results_dir)
                    with open(train_pred_fp, 'rb') as handle:
                        train_pred_dict = pickle.load(handle)
                    model_data.update_training_df_with_preds(train_pred_dict)
                except FileNotFoundError:
                    print("WARNING: no predictions on training set.")

            # append model_data to list
            model_data_list.append(model_data)
        self.model_data_list = model_data_list
