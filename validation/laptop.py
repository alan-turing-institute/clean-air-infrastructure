"""
Run a validation experiment locally on your laptop.
"""

import experiment

class LaptopExperiment(experiment.SVGPExperiment):
    """
    Run a simple experiment on your laptop with an SVGP.
    """

    def __init__(self, name, **kwargs):
        # model_params = self.get_default_model_params()
        # data_config = self.get_default_data_config()
        # super().__init__(name, 'laptop', model_params=model_params, data_config=data_config)
        super().__init__(name, 'laptop')

    def get_default_model_params(self):
        model_params = super().get_default_model_params()
        model_params['lengthscale'] = [0.1]
        model_params['variance'] = [0.1]
        model_params['max_iter'] = [10000]
        model_params['n_inducing_points'] = [100, 200]
        return model_params

    def get_default_data_config(self, n_rolls=2):
        data_config = super().get_default_data_config(n_rolls=n_rolls)
        for index in range(len(data_config)):
            data_config[index]["features"] = ['value_1000_flat']
        return data_config
