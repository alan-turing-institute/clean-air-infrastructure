"""
A module for satellite experiments.
"""

from abc import abstractmethod
import pandas as pd
from . import experiment

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
        return []
