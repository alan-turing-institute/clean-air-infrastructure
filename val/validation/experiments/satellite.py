"""
A module for satellite experiments.
"""

from abc import abstractmethod
from . import experiment
from .. import util

import copy


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
        dgp_default = get_dgp_default_config()
        dgp_default['id'] = 0

        dgp_default_se = copy.deepcopy(dgp_default)
        dgp_default_se['id'] = 1
        dgp_default_se['dgp_sat']['kernel'] = [{
            "name": "MR_SE_SAT_DGP",
            "type": "se",
            "active_dims": [0],  # previous GP, lat, lon, value_1000_flat
            "lengthscales": [0.1],
            "variances": [1.0],
        }]



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
            'mr_dgp' : [
                dgp_default
            ],
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
            data_config[index]["features"] = 'all'
            data_config[index]['include_satellite'] = True
            data_config[index]['train_satellite_interest_points'] = 'all'
            data_config[index]['train_sources'] = ['laqn']
            data_config[index]['pred_sources'] = ['laqn', 'hexgrid']
        return data_config


def get_dgp_default_config():
    return {
        "restore": False,
        "train": True,
        "model_state_fp": "",
        "base_laqn": {
            "kernel": {
                "name": "MR_SE_LAQN_BASE",
                "type": "se",
                "active_dims": [0, 1, 2, 3],  # epoch, lat, lon, feature
                "lengthscales": [0.1, 0.1, 0.1, 0.1],
                "variances": [1.0, 1.0, 1.0, 1.0],
            },
            "inducing_num": 300,
            "minibatch_size": 100,
            "noise_sigma": 0.1,
        },
        "base_sat": {
            "kernel": {
                "name": "MR_SE_SAT_BASE",
                "type": "se",
                "active_dims": [0, 1, 2],  # epoch, lat, lon
                "lengthscales": [0.1, 0.1, 0.1],
                "variances": [1.0, 1.0, 1.0],
            },
            "inducing_num": 300,
            "minibatch_size": 100,
            "noise_sigma": 0.1,
        },
        "dgp_sat": {
            "kernel": [
                {
                    "name": "MR_LINEAR_SAT_DGP",
                    "type": "linear",
                    "active_dims": [0],  # previous GP
                    "variances": [1.0],
                },
                {
                    "name": "MR_SE_SAT_DGP",
                    "type": "se",
                    "active_dims": [2, 3, 4],  # lat, lon, feature
                    "lengthscales": [0.1, 0.1, 0.1],
                    "variances": [1.0, 1.0, 1.0],
                },
            ],
            "inducing_num": 300,
            "minibatch_size": 100,
            "noise_sigma": 0.1,
        },
        "mixing_weight": {"name": "dgp_only", "param": None},
        "num_samples_between_layers": 1,
        "num_prediction_samples": 10,
    }
