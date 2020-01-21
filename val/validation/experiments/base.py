from abc import ABC, abstractmethod
import pandas as pd
import pathlib
from ..cluster import *

class Experiment():
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

    @abstractmethod
    def get_default_experiment_df(self):
        """
        Get all the default experiment configurations.
        """

    def setup(self, experiment_data_dir='experiment_data/', secret_fp="../terraform/.secrets/db_secrets.json", force_redownload=False):
        """
        Given an experiment create directories, data and files.
        """
        # create directories if they don't exist
        exp_dir = experiment_data_dir + self.name + '/'
        pathlib.Path(experiment_data_dir).mkdir(exist_ok=True)
        pathlib.Path(exp_dir).mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'results').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'data').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'meta').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'models').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'models/restore').mkdir(exist_ok=True)

        # load and write model data objects to files
        pass

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
