"""
A simple experiment.
"""

from .experiment import Experiment
from . import util

class BasicExperiment(Experiment):
    """
    A basic experiment on just air quality sensors.
    """

    def __init__(self, name, models, cluster_name, **kwargs):
        super().__init__(name, models, cluster_name, **kwargs)
        if 'model_params' not in kwargs:
            self.model_params = self.get_default_model_params()
        if 'data_config' not in kwargs:
            self.data_config = self.get_default_data_config()
        if 'experiment_df' not in kwargs:
            self.experiment_df = self.get_default_experiment_df()        

    def get_default_model_params(self):
        return {'svgp' : create_params_list(
            lengthscale=[0.1, 0.5],
            variance=[0.1, 0.5],
            minibatch_size=[100],
            n_inducing_points=[30],
            max_iter=[100],
            refresh=[10],
            train=[True],
            restore=[False],
            laqn_id=[0]
        )}

    def get_default_data_config(self, n_rolls=1):
        # create dates for rolling over
        train_start = "2019-11-01T00:00:00"
        train_n_hours = 48
        pred_n_hours = 24
        rolls = util.create_rolls(train_start, train_n_hours, pred_n_hours, n_rolls)
        data_dir = '../run_model/experiments/{name}/data/'.format(name=self.name)
        data_config = util.create_data_list(rolls, data_dir)
        return data_config
