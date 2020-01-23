"""
Run a validation experiment locally on your laptop.
"""
import sys
sys.path.append('../')
import experiment

class LaptopExperiment(experiment.SVGPExperiment):
    """
    Run a simple experiment on your laptop with an SVGP.
    """

    def __init__(self, name, **kwargs):
        # model_params = self.get_default_model_params()
        # data_config = self.get_default_data_config()
        # super().__init__(name, 'laptop', model_params=model_params, data_config=data_config)
        super().__init__(name, 'laptop', **kwargs)

    def get_default_model_params(self):
        """
        Try two different configs with different number of inducing points.
        """
        return {'svgp' : experiment.create_params_list(
            lengthscale=[0.1],
            variance=[0.5],
            minibatch_size=[100],
            n_inducing_points=[30, 300],
            max_iter=[10000],
            refresh=[10],
            train=[True],
            restore=[False],
            laqn_id=[0]
        )}

    def get_default_data_config(self, n_rolls=2):
        """
        Roll for 2 days with four features:
        epoch, lat, lon, and value_1000_flat.

        Predict for 2 day training period and 1 day testing period.
        """
        data_config = super().get_default_data_config(n_rolls=n_rolls)
        for index in range(len(data_config)):
            data_config[index]["features"] = ['value_1000_flat']
            data_config[index]["pred_start_date"] = data_config[index]["train_start_date"]
        return data_config

def get_experiment():
    exp = LaptopExperiment('laptop')
    return exp


if __name__ == "__main__":
    exp = get_experiment()
    exp.setup()
