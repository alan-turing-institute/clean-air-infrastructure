"""
A module for satellite experiments.
"""

from abc import abstractmethod
from . import experiment
from .. import util

class SatelliteExperiment(experiment.Experiment):
    """
    An experiment with Satellite data.
    """

    def __init__(self, name, models, cluster_name, **kwargs):
        models =  list(self.get_default_model_params().keys())
        super().__init__(name, models, cluster_name, **kwargs)
        if 'data_config' not in kwargs:
            self.data_config = self.get_default_data_config()
        if 'model_params' not in kwargs:    # ToDo: remove these two lines
            self.model_params = self.get_default_model_params()
        if 'experiment_df' not in kwargs:
            self.experiment_df = self.get_default_experiment_df()

    # @abstractmethod
    def get_default_model_params(self):
        """
        Get model parameters for an experiment on satellite data.
        """
        # ToDo: this method should be abstract
        # ToDo: this assumes an SVGP but this will not work in practise
        return {
            'svgp' : util.create_params_list(
                lengthscale=[0.1],
                variance=[0.1],
                minibatch_size=[100],
                n_inducing_points=[30],
                max_iter=[100],
                refresh=[10],
                train=[True],
                restore=[False],
                laqn_id=[0]
            ),
            'mr_gprn' : util.create_params_list(
                lengthscale=[0.1],
                variance=[0.1],
                minibatch_size=[100],
                n_inducing_points=[200],
                max_iter=[100],
                refresh=[10],
                train=[True],
                restore=[False],
                laqn_id=[0]
            ),
            'mr_dgp' : util.create_params_list(
                lengthscale=[0.1],
                variance=[0.1],
                minibatch_size=[100],
                n_inducing_points=[200],
                max_iter=[100],
                refresh=[10],
                train=[True],
                restore=[False],
                laqn_id=[0]
            ),
        }

    def get_default_experiment_df(self):
        # ToDo: does this method need to be overwritten for satellite data?
        return super().get_default_experiment_df()

    def get_default_data_config(self):
        # create dates for rolling over
        n_rolls = 1
        train_start = "2020-02-01T00:00:00"
        train_n_hours = 48
        pred_n_hours = 24
        rolls = util.create_rolls(train_start, train_n_hours, pred_n_hours, n_rolls)
        data_dir = '{dir}{name}/data/'.format(dir=self.experiments_directory, name=self.name)
        data_config = util.create_data_list(rolls, data_dir)
        for index in range(len(data_config)):
            data_config[index]["features"] = ['value_1000_flat']
            data_config[index]['include_satellite'] = True
            data_config[index]['train_satellite_interest_points'] = 'all'
            data_config[index]['train_sources'] = ['laqn']
            data_config[index]['pred_sources'] = ['laqn', 'hexgrid']
        return data_config
