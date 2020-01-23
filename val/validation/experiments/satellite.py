"""
A module for satellite experiments.
"""

from abc import abstractmethod
import pandas as pd
from . import experiment
from .. import util

class SatelliteExperiment(experiment.Experiment):
    """
    An experiment with Satellite data.
    """

    def __init__(self, experiment_name, models, cluster_name, **kwargs):
        super().__init__(experiment_name, models, cluster_name, **kwargs)
        if 'data_config' not in kwargs:
            self.data_config = self.get_default_data_config()
        if 'experiment_df' not in kwargs:
            self.experiment_df = self.get_default_experiment_df()

    @abstractmethod
    def get_default_model_params(self):
        """
        Get model parameters for an experiment on satellite data.
        """

    def get_default_experiment_df(self):
        return pd.DataFrame()

    def get_default_data_config(self):
        # create dates for rolling over
        train_start = "2019-11-01T00:00:00"
        train_n_hours = 48
        pred_n_hours = 24
        rolls = util.create_rolls(train_start, train_n_hours, pred_n_hours, n_rolls)
        data_dir = '{dir}{name}/data/'.format(dir=self.directory, name=self.name)
        data_config = util.create_data_list(rolls, data_dir)
        for index in range(len(data_config)):
            data_config[index]["features"] = ['value_1000_flat']
            data_config[index]['use_satellite'] = True
            data_config[index]['train_satellite_interest_points'] = 'all'
        return data_config
