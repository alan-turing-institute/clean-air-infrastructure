"""
A simple experiment.
"""

from .experiment import Experiment
from .. import util

class BasicExperiment(Experiment):
    """
    A basic experiment on just air quality sensors with an SVGP.
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
        return {'svgp_tf1' : util.create_params_list(
            lengthscale=[0.1],
            variance=[0.1],
            minibatch_size=[100],
            n_inducing_points=[30],
            maxiter=[1],
            refresh=[10],
            train=[True],
            restore=[False],
            jitter=[1e-5],
            model_state_fp=[None],
        )}

    def get_default_data_config(self, **kwargs):
        # initial parameters and dates
        train_start = "2019-11-01T00:00:00" if 'train_start' not in kwargs else kwargs['train_start']
        train_n_hours = 48 if 'train_n_hours' not in kwargs else kwargs['train_n_hours']
        pred_n_hours = 24 if 'pred_n_hours' not in kwargs else kwargs['pred_n_hours']
        num_rolls = 1 if 'num_rolls' not in kwargs else kwargs['num_rolls']

        # create dates for rolling over
        rolls = util.create_rolls(train_start, train_n_hours, pred_n_hours, num_rolls)

        # create the data config file
        data_dir = '{dir}{name}/data/'.format(dir=self.experiments_directory, name=self.name)
        data_config = util.create_data_list(rolls, data_dir)
        for index in range(len(data_config)):
            data_config[index]["features"] = ['value_1000_flat']
        return data_config
