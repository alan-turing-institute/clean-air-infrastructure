import pandas as pd
import itertools

# validation modules
import parameters

class Experiment():

    def __init__(self, experiment_name, model_name, cluster_name, **kwargs):
        """
        kwargs
        ___

        model_params : list of dicts
        data_config : list of dicts
        """
        self.name = experiment_name
        self.model_name = model_name
        self.cluster = cluster_name
        self.model_params = kwargs['model_params'] if 'model_params' in kwargs else []
        self.data_config = kwargs['data_config'] if 'data_config' in kwargs else []

    def create_experiments_df(self):
        experiment_configs = {
            'model_name':[self.model_name],
            'param_id':[item['id'] for item in self.model_params],
            'data_id':[item['id'] for item in self.data_config],
            'cluster':[self.cluster]
        }
        list_of_configs = [values for key, values in experiment_configs.items()]
        params_configs = list(itertools.product(*list_of_configs))
        experiments_df = pd.DataFrame(params_configs, columns=experiment_configs.keys())

        experiments_df['y_pred_fp'] = pd.Series([create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + 'y_pred.npy' for r in experiments_df.itertuples()])

        experiments_df['y_var_fp'] = pd.Series([create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + 'y_var.npy' for r in experiments_df.itertuples()])

        experiments_df['model_state_fp'] = pd.Series([create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + '.model' for r in experiments_df.itertuples()])

        return experiments_df

class SVGPExperiment(Experiment):

    def __init__(self, experiment_name, cluster_name, **kwargs):
        super().__init__(experiment_name, 'svgp', cluster_name, **kwargs)

    def get_default_model_params_list(self, lengthscale=[0.1], variance=[0.1], minibatch_size=[100], n_inducing_point=[3000]):
        return parameters.create_params_dict(
            lengthscale=lengthscale,
            variance=variance,
            minibatch_size=minibatch_size,
            n_inducing_point=n_inducing_point
        )



def create_experiment_prefix(model_name, param_id, data_id, base_dir='results/'):
    return base_dir + model_name + '_param' + str(param_id) + '_data' + str(data_id) + '_'

def get_model_data_config_default(id, train_start, train_end, pred_start, pred_end, train_points='all', pred_points='all'):
    return {
        'id': id,
        'train_start_date': train_start,
        'train_end_date': train_end,
        'pred_start_date': pred_start,
        'pred_end_date': pred_end,
        'train_sources': ['laqn', 'aqe'],
        'pred_sources': ['laqn', 'aqe'],
        'train_interest_points': train_points,
        'pred_interest_points': pred_points,
        'species': ['NO2'],
        'features': 'all',
        'norm_by': 'laqn',
        'model_type': 'svgp',
        'tag': 'testing'
    }

def create_data_dict(rolls):

    data_config_dict = [
        get_model_data_config_default(
            i, rolls[i]['train_start_date'], rolls[i]['train_end_date'],
            rolls[i]['pred_start_date'], rolls[i]['pred_end_date']
        ) for i in range(len(rolls))
    ]

    for datatype in ['x_train', 'x_test', 'y_train', 'y_test']:
        for i in range(len(rolls)):
            data_config_dict[i][datatype + '_fp'] = create_data_filepath(i, datatype)

    return data_config_dict
    
def create_data_filepath(index, basename, base_dir='data/', extension='.npy'):
    return base_dir + 'data' + str(index) + '_' + basename + extension
