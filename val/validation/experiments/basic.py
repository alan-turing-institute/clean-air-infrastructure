"""
A simple experiment.
"""

from .experiment import Experiment
from .. import util

class BasicExperiment(Experiment):
    """
    A basic experiment on just air quality sensors with an SVGP.
    """

    def __init__(self, experiment_name, models, cluster_name, **kwargs):
        super().__init__(experiment_name, models, cluster_name, **kwargs)
        if 'model_params' not in kwargs:
            self.model_params = self.get_default_model_params()
        if 'data_config' not in kwargs:
            self.data_config = self.get_default_data_config()
        if 'experiment_df' not in kwargs:
            self.experiment_df = self.get_default_experiment_df()        

    def get_default_model_params(self):
        return {'svgp' : util.create_params_list(
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

    def get_default_data_config(self):
        # create dates for rolling over
        n_rolls = 1
        train_start = "2019-11-01T00:00:00"
        train_n_hours = 48
        pred_n_hours = 24
        rolls = util.create_rolls(train_start, train_n_hours, pred_n_hours, n_rolls)
        data_dir = '{dir}{name}/data/'.format(dir=self.directory, name=self.name)
        data_config = util.create_data_list(rolls, data_dir)
        for index in range(len(data_config)):
            data_config[index]["features"] = ['value_1000_flat']
        return data_config
