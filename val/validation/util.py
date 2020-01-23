"""
Useful functions for experiments.
"""

import os
import json
import itertools
import importlib
import inspect
import pandas as pd
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta

def pickle_files_exist(data_config):
    return os.path.exists(data_config['train_fp']) and os.path.exists(data_config['test_fp'])

def load_experiment_from_directory(name, experiment_data='experiment_data/'):
    """
    Return an experiment with a name from a directory.

    Parameters
    ___

    name : str
        Name of the experiment.

    experiment_data : str
        Filepath to the directory containing all experiments.

    Returns
    ___

    Experiment
        Initialised from directory.
    """
    directory = experiment_data + name + '/'

    with open(directory + 'meta/model_params.json', 'r') as fp:
        model_params = json.load(fp)

    with open(directory + 'meta/data.json', 'r') as fp:
        data_config = json.load(fp)

    experiment_df = pd.read_csv(directory + 'meta/experiment.csv', index_col=0)

    models = list(experiment_df['model_name'].unique())
    cluster_name = list(experiment_df['cluster'].unique())[0]

    return get_experiment_class(name)(name, models, cluster_name, model_params=model_params, data_config=data_config, experiment_df=experiment_df, directory=experiment_data)
    
def get_experiment_class(name):
    """
    Get the class of experiment given the name.

    Parameters
    ___

    name : str
        Name of the experiment.

    Returns
    ___

    class
        A class object that is ready to be initialised.
    """
    mod = importlib.import_module('validation.experiments.{name}'.format(name=name), 'validation')
    members = inspect.getmembers(mod, inspect.isclass)

    class_index = -1
    for i in range(len(members)):
        if members[i][0].lower() == '{name}experiment'.format(name=name):
            class_index = i

    if class_index < 0:
        raise FileNotFoundError("Class for {name} does not exist.".format(name=name))

    return members[class_index][1]

def create_experiment_prefix(model_name, param_id, data_id):
    """
    Create a unique prefix for a run/result of an experiment.

    Parameters
    ___

    model_name : str
        Name should refer to a model class.

    param_id : int
        Id of parameter setting for given model.

    data_id : int
        Id of a data config.

    Returns
    ___

    str
        Prefix for files.
    """
    return model_name + '_param' + str(param_id) + '_data' + str(data_id)

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
        'tag': 'validation',
        'include_satellite':False,
        'include_prediction_y':True,
        'train_satellite_interest_points':'all'
    }

def create_data_list(rolls, data_dir, extension='.pickle'):
    """
    Get a list of data configurations.

    Parameters
    ___

    rolls : list of dicts
        Each dict has the training start time, training end time,
        prediction start time, prediction end time of the data roll.

    data_dir : str
        The directory to which the data should be saved.

    Returns
    ___

    list of dicts
        List of data configurations.
    """

    data_config_list = [
        get_model_data_config_default(
            i, rolls[i]['train_start_date'], rolls[i]['train_end_date'],
            rolls[i]['pred_start_date'], rolls[i]['pred_end_date']
        ) for i in range(len(rolls))
    ]

    for datatype in ['train', 'test']:
        for i in range(len(rolls)):
            data_config_list[i][datatype + '_fp'] = create_data_filepath(i, datatype, base_dir=data_dir, extension=extension)

    return data_config_list
    
def create_data_filepath(index, basename, base_dir='data/', extension='.pickle'):
    """
    Create a filepath for a data file, e.g. numpy array.

    Parameters
    ___

    index : int
        Id of the data configuration.

    basename : str
        e.g. 'y_pred', 'x_test'

    base_dir : str, optional
        The directory to store the data file in.

    extension : str, optional
        The data type of the file, e.g. csv, npy.

    Returns
    ___

    str
        Filepath of the data file.
    """
    return base_dir + 'data' + str(index) + '/' + basename + extension

def create_params_list(**kwargs):
    """
    Return a list of dicts with every possible parameter configuration.

    Parameters
    ___

    kwargs : dict
        For each key-value pair, the value should be a list.
        The product of all ordered lists is computed.

    Returns
    ___

    list of dicts
        All possible parameter configs stored in a list.
    """
    keys = list(kwargs.keys())
    list_of_params = [values for key, values in kwargs.items()]
    params_configs = list(itertools.product(*list_of_params))
    params_list = [
        {
            keys[j] : params_configs[i][j] for j in range(len(keys))
        } for i in range(len(params_configs))
    ]
    for i in range(len(params_list)):
        params_list[i]['id'] = i
    return params_list

def create_rolls(train_start, train_n_hours, pred_n_hours, num_rolls):
    """
    Create a list of dictionaries with train and pred dates rolled up.
    """
    start_of_roll = train_start
    rolls = []

    for i in range(num_rolls):

        train_end = strtime_offset(start_of_roll, train_n_hours)
        pred_start = strtime_offset(start_of_roll, train_n_hours)
        pred_end = strtime_offset(pred_start, pred_n_hours)
        rolls.append({
            'train_start_date': start_of_roll,
            'train_end_date': train_end,
            'pred_start_date': pred_start,
            'pred_end_date': pred_end
        })
        start_of_roll = strtime_offset(start_of_roll, pred_n_hours)
    
    return rolls

def strtime_offset(strtime, offset_hours):
    """Give an datetime as an iso string and an offset and return a new time"""

    return (isoparse(strtime) + relativedelta(hours=offset_hours)).isoformat()

def dict_without_key(dict_obj, key):
    """
        Return a dictionary with the key removed.
    """
    new_dict_obj = dict_obj.copy()
    new_dict_obj.pop(key)
    return new_dict_obj

def ensure_last_backslash(dir_str):
    """
        Ensure directory ends in a backslash
    """
    if dir_str[-1] is not '/':
        return dir_str+'/'
    return dir_str
