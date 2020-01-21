"""
The base class for experiments.
"""

import sys
import json
from abc import ABC, abstractmethod
import pandas as pd
import pathlib
import itertools

from . import util

#requires cleanair
sys.path.append("../containers/")
sys.path.append("../../containers/")

try:
    from cleanair.models import ModelData
except:
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

        experiment_df['y_pred_fp'] = pd.Series([
            self.directory + '{name}/results/'.format(name=self.name) + util.create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + '_y_pred.npy' for r in experiment_df.itertuples()])

        experiment_df['model_state_fp'] = pd.Series([
            self.directory + '{name}/models/restore/m_{model_name}'.format(name=self.name, model_name=r.model_name) + util.create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + '.model' for r in experiment_df.itertuples()])

        return experiment_df

    def setup(self, secret_fp="../terraform/.secrets/db_secrets.json", force_redownload=False):
        """
        Given an experiment create directories, data and files.
        """
        self.__create_experiment_data_directories()

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
        Create directories if they don't exist.
        """
        exp_dir = self.directory + self.name + '/'
        pathlib.Path(self.directory).mkdir(exist_ok=True)
        pathlib.Path(exp_dir).mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'results').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'data').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'meta').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'models').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'models/restore').mkdir(exist_ok=True)

    def run(self):
        """
        Run the experiment.
        """
        pass

    def check_status(self):
        """
        Check the status of an experiment on a cluster.
        """
        pass

    def update_model_data_list(self):
        """
        Update the model data list.
        """
        pass