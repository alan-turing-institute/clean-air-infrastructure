import pandas as pd
import itertools

def create_experiments_df(model_name=['svgp'], param_id=[0], data_id=[0], cluster=['pearl']):
    experiment_configs = {
        'model_name':model_name,
        'param_id':param_id,
        'data_id':data_id,
        'cluster':cluster
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

def create_experiment_prefix(model_name, param_id, data_id, base_dir='results/'):
    return base_dir + model_name + '_param' + str(param_id) + '_data' + str(data_id) + '_'

def get_model_data_config_default(train_start, train_end, pred_start, pred_end, train_points='all', pred_points='all'):
    return {
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

    data_config_dict = {
        i : get_model_data_config_default(
            rolls[i]['train_start_date'], rolls[i]['train_end_date'],
            rolls[i]['pred_start_date'], rolls[i]['pred_end_date']
        ) for i in range(len(rolls))
    }

    for datatype in ['x_train', 'x_test', 'y_train', 'y_test']:
        for i in range(len(rolls)):
            data_config_dict[i][datatype + '_fp'] = create_data_filepath(i, datatype)

    return data_config_dict
    
def create_data_filepath(index, basename, base_dir='data/', extension='.npy'):
    return base_dir + 'data' + str(index) + '_' + basename + extension
