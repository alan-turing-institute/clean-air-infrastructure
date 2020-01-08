import pandas as pd
import itertools

def create_experiments_df():
    experiment_configs = {
        'model_name':['svgp'],
        'param_id':[0,1,2,3],
        'data_id':[0,1,2]
    }
    list_of_configs = [values for key, values in experiment_configs.items()]
    params_configs = list(itertools.product(*list_of_configs))
    experiments_df = pd.DataFrame(params_configs, columns=experiment_configs.keys())

    print(experiments_df)

    experiments_df['y_pred_fp'] = pd.Series([create_experiment_filepath(
            r.model_name, r.param_id, r.data_id
        ) for r in experiments_df.itertuples()])

    experiments_df['y_var_fp'] = pd.Series([create_experiment_filepath(
            r.model_name, r.param_id, r.data_id, base_filename='y_var'
        ) for r in experiments_df.itertuples()])

    experiments_df['model_state_fp'] = pd.Series([create_experiment_filepath(
            r.model_name, r.param_id, r.data_id, base_filename='model_state', extension='.model'
        ) for r in experiments_df.itertuples()])

    return experiments_df

def create_experiment_filepath(model_name, param_id, data_id, base_dir='results/', base_filename='y_pred_fp', extension='.npy'):
    return base_dir + model_name + '_param' + str(param_id) + '_data' + str(data_id) + '_' + base_filename + extension

def create_data_df(rolls):
    data_df = pd.DataFrame(columns=['train_start_date', 'train_end_date', 'pred_start_date', 'pred_end_date'])
    for roll in rolls:
        data_df = data_df.append(roll, ignore_index=True)

    for datatype in ['x_train', 'x_test', 'y_train', 'y_test']:
        data_df[datatype + '_fp'] = pd.Series([create_data_filepath(
            i, datatype
        ) for i in range(data_df.shape[0])])

    return data_df
    
def create_data_filepath(index, basename, base_dir='data/', extension='.npy'):
    return base_dir + 'data' + str(index) + '_' + basename + extension
