"""
Run a validation experiment locally on your laptop.
"""

import experiment

class LaptopExperiment(experiment.SVGPExperiment):

    def __init__(self, name, **kwargs):
        """
        Run a simple experiment on your laptop with an SVGP.
        """
        super().__init__(name, ['svgp'], 'laptop', **kwargs)

    def get_default_model_params(self):
        model_params = super().get_default_model_params()
        model_params['lengthscale'] = [0.1]
        model_params['variance'] = [0.1]
        model_params['max_iter'] = [10000]
        model_params['n_inducing_points'] = [100, 200]
        return model_params

    def get_default_data_config(self):
        data_config = super().get_default_data_config()