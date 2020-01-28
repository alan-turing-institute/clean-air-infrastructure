"""
A basic SVGP experiment.
"""

from . import basic
from .. import util

class BasicSvgpExperiment(basic.BasicExperiment):

    def __init__(self, name, models, cluster_name, **kwargs):
        super().__init__(name, models, cluster_name, **kwargs)

    def get_default_model_params(self):
        return {'svgp' : util.create_params_list(
            lengthscale=[0.1, 2],
            variance=[0.1],
            minibatch_size=[100],
            n_inducing_points=[30, 10],
            max_iter=[1000],
            refresh=[10],
            train=[True],
            restore=[False],
            laqn_id=[0]
        )}
