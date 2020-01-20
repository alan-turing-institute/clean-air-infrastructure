import sys
sys.path.append('../')

import experiment
import temporal

class GridExperiment(experiment.SVGPExperiment):
    def get_default_model_params(self):
        """
        Try two different configs with different number of inducing points.
        """
        return {
            'svgp' : experiment.create_params_list(
                lengthscale=[0.1],
                variance=[0.5],
                minibatch_size=[1000],
                n_inducing_points=[500],
                max_iter=[20000],
                refresh=[100],
                train=[True],
                restore=[False],
                laqn_id=[0]
            )
        }

    def get_default_data_config(self, n_rolls=1):
        """
        Roll for 2 days with four features:
        epoch, lat, lon, and value_1000_flat.
        """

        train_start = "2019-11-01T00:00:00"
        train_n_hours = 48
        pred_n_hours = 24
        n_rolls = 1

        rolls = temporal.create_rolls(train_start, train_n_hours, pred_n_hours, n_rolls)
        data_dir = '../../run_model/experiments/{name}/data/'.format(name=self.name)
        data_config = experiment.create_data_list(rolls, data_dir, extension='.pickle')

        for index in range(len(data_config)):
            data_config[index]["features"] = ['value_1000_flat']
            data_config[index]["train_sources"] = ['laqn', 'hexgrid']
            data_config[index]["pred_sources"] = ['laqn', 'hexgrid']
        return data_config

def get_experiment():
    exp = GridExperiment('grid_exp', 'pearl')
    return exp

if __name__ == "__main__":
    exp = get_experiment()
    exp.setup(base_dir='../../run_model/experiments/', secret_fp="../../terraform/.secrets/db_secrets.json", force_redownload=True)
