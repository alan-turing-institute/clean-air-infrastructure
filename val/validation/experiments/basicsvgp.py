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
            lengthscale=[0.1],
            variance=[0.1],
            minibatch_size=[100],
            n_inducing_points=[30, 300],
            max_iter=[10000],
            refresh=[10],
            train=[True],
            restore=[False],
            laqn_id=[0]
        )}

    def get_default_data_config(self):
        """
        Returns four different data configs with 7, 5, 3, 2 days
        of training data respectively.
        Every data config predicts on 2 days of data.

        All the data configs use the `value_1000_flat` and `value_1000_total_road_length` features.
        """
        data_config = super().get_default_data_config(
            train_start="2020-01-01T00:00:00",
            num_rolls=1,
            train_n_hours=7*24,     # train for 7 days
            pred_n_hours=48         # predict on 2 days
        )
        data_config.extend(super().get_default_data_config(
            train_start="2020-01-03T00:00:00",
            num_rolls=1,
            train_n_hours=5*24,     # train for 5 days
            pred_n_hours=48         # predict on 2 days            
        ))
        data_config.extend(super().get_default_data_config(
            train_start="2020-01-05T00:00:00",
            num_rolls=1,
            train_n_hours=3*24,     # train for 3 days
            pred_n_hours=48         # predict on 2 days            
        ))
        data_config.extend(super().get_default_data_config(
            train_start="2020-01-06T00:00:00",
            num_rolls=1,
            train_n_hours=2*24,     # train for 2 days
            pred_n_hours=48         # predict on 2 days            
        ))

        # overwrite previous settings to update ids
        for index in range(len(data_config)):
            data_config[index]['id'] = index
            data_config[index]["features"] = ['value_1000_flat', 'value_1000_total_road_length']
            data_config[index]['train_fp'] = '{dir}{name}/data/data{id}/train.pickle'.format(
                dir=self.experiments_directory, name=self.name, id=index
            )
            data_config[index]['test_fp'] = '{dir}{name}/data/data{id}/test.pickle'.format(
                dir=self.experiments_directory, name=self.name, id=index
            )
        return data_config
