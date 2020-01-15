"""
Class and methods for experiments.
"""

from abc import ABC, abstractmethod
import sys
import json
import pandas as pd
import numpy as np
import itertools
import pathlib
import os

# validation modules
import temporal

# requires cleanair
sys.path.append("../containers")
try:
    from cleanair.models import ModelData
except:
    pass

class Experiment(ABC):

    def __init__(self, experiment_name, models, cluster_name, **kwargs):
        """
        An abstract experiment class.

        Parameters
        ___

        experiment_name : str
            Name that identifies the experiment.

        models : list
            List of string identifying the models to run in the experiment.

        cluster_name : str 
            String to identify the cluster the experiment was ran on.

        model_params : list of dicts
            A list of model parameter configurations.
            Each model config is a dictionary.

        data_config : list of dicts
            A list of data configurations.
            Each config is a dictionary.

        experiment_df : DataFrame
            A dataframe describing every run in the experiment.
        """
        super().__init__()
        self.name = experiment_name
        self.models = models
        self.cluster = cluster_name
        self.model_params = kwargs['model_params'] if 'model_params' in kwargs else []
        self.data_config = kwargs['data_config'] if 'data_config' in kwargs else []
        self.experiment_df = kwargs['experiment_df'] if 'experiment_df' in kwargs else pd.DataFrame()

    @abstractmethod
    def get_default_model_params(self):
        """
        Get the default parameters of the model for this experiment.
        """

    @abstractmethod
    def get_default_data_config(self):
        """
        Get the default data configurations for this experiment.
        """

    @abstractmethod
    def get_default_experiment_df(self):
        """
        Get all the default experiment configurations.
        """

    def setup(self, base_dir='../run_model/experiments/', secret_fp="../terraform/.secrets/db_secrets.json"):
        """
        Given an experiment create directories, data and files.
        """
        # create directories if they don't exist
        exp_dir = base_dir + self.name + '/'
        pathlib.Path(base_dir).mkdir(exist_ok=True)
        pathlib.Path(exp_dir).mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'results').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'data').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'meta').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'models').mkdir(exist_ok=True)

        # store a list of ModelData objects to validate over
        model_data_list = []

        # create ModelData objects for each roll
        for index, row in self.experiment_df.iterrows():
            data_id = row['data_id']
            data_config = self.data_config[data_id]

            # If the numpy files do not exist locally
            if not numpy_files_exist(data_config):
                # make new directory for data
                data_dir_path = exp_dir + 'data/data{id}'.format(id=data_id)
                pathlib.Path(data_dir_path).mkdir(exist_ok=True)

                # Get the model data and append to list
                model_data = ModelData(config=data_config, secretfile=secret_fp)
                model_data_list.append(model_data)

                # save config status of the model data object to the data directory
                # model_data.save_config_state(data_dir_path)

                print("x train shape:", model_data.get_training_data_arrays()['X'].shape)
                print("y train shape:", model_data.get_training_data_arrays()['Y'].shape)
                print("x test shape:", model_data.get_pred_data_arrays(return_y=True)['X'].shape)
                print("y test shape:", model_data.get_pred_data_arrays(return_y=True)['Y'].shape)
                print()
                print("x test shape without return_y:", model_data.get_pred_data_arrays(return_y=True)['X'].shape)
                print()
                if model_data.get_training_data_arrays()['X'].shape[0] != model_data.get_training_data_arrays()['Y'].shape[0]:
                    raise Exception("training X and Y not the same length")

                if model_data.get_pred_data_arrays(return_y=True)['X'].shape[0] != model_data.get_pred_data_arrays(return_y=True)['Y'].shape[0]:
                    raise Exception("testing X and Y not the same length")

                # save normalised data to numpy arrays
                np.save(data_config['x_train_fp'], model_data.get_training_data_arrays()['X'])
                np.save(data_config['y_train_fp'], model_data.get_training_data_arrays()['Y'])
                np.save(data_config['x_test_fp'], model_data.get_pred_data_arrays(return_y=True)['X'])
                np.save(data_config['y_test_fp'], model_data.get_pred_data_arrays(return_y=True)['Y'])

        # save experiment dataframe to csv
        self.experiment_df.to_csv(exp_dir + 'meta/experiment.csv')

        # save data and params configs to json
        with open(exp_dir + 'meta/data.json', 'w') as fp:
            json.dump(self.data_config, fp, indent=4)

        with open(exp_dir + 'meta/model_params.json', 'w') as fp:
            json.dump(self.model_params, fp, indent=4)

class SVGPExperiment(Experiment):

    def __init__(self, experiment_name, cluster_name, **kwargs):
        super().__init__(experiment_name, ['svgp'], cluster_name, **kwargs)
        if 'model_params' not in kwargs:
            self.model_params = self.get_default_model_params()
        if 'data_config' not in kwargs:
            self.data_config = self.get_default_data_config()
        if 'experiment_df' not in kwargs:
            self.experiment_df = self.get_default_experiment_df()        

    def get_default_model_params(self):
        return {'svgp' : create_params_list(
            lengthscale=[0.1, 0.5],
            variance=[0.1, 0.5],
            minibatch_size=[100],
            n_inducing_points=[30],
            max_iter=[100],
            refresh=[10],
            train=[True],
            restore=[False],
            laqn_id=[0]
        )}

    def get_default_data_config(self):
        # create dates for rolling over
        train_start = "2019-11-01T00:00:00"
        train_n_hours = 48
        pred_n_hours = 24
        n_rolls = 1
        rolls = temporal.create_rolls(train_start, train_n_hours, pred_n_hours, n_rolls)
        data_dir = '../run_model/experiments/{name}/data/'.format(name=self.name)
        data_config = create_data_list(rolls, data_dir)
        return data_config

    def get_default_experiment_df(self, experiments_root='../run_model/experiments/'):
        """
        Create a dataframe where each line is one run/result of an experiment.

        Parameters
        ___

        experiments_root : str, optional
            The root directory containing all experiments.
        """
        cols = ['model_name', 'param_id', 'data_id', 'cluster']
        experiment_df = pd.DataFrame(columns=cols)

        for model_name in self.models:
            # configs for this model
            experiment_configs = {
                'model_name':[model_name],
                'param_id':[item['id'] for item in self.model_params[model_name]],
                'data_id':[item['id'] for item in self.data_config],
                'cluster':[self.cluster]
            }
            list_of_configs = [values for key, values in experiment_configs.items()]
            params_configs = list(itertools.product(*list_of_configs))

            # append to experiments dataframe
            experiment_df = experiment_df.append(pd.DataFrame(params_configs, columns=cols), ignore_index=True)

        experiment_df['y_pred_fp'] = pd.Series([
            experiments_root + '{name}/results/'.format(name=self.name) + create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + '_y_pred.npy' for r in experiment_df.itertuples()])



        experiment_df['model_state_fp'] = pd.Series([
            experiments_root + '{name}/results/'.format(name=self.name) + create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + '.model' for r in experiment_df.itertuples()])

        return experiment_df

def experiment_from_dir(name, cluster_name, experiment_dir='../run_model/experiments/'):
    """
    Return an experiment with a name from a directory.

    Parameters
    ___

    name : str
        Name of the experiment.

    experiment_dir : str
        Filepath to the directory containing all experiments.

    Returns
    ___

    Experiment
        Read from files.
    """
    # load the experiments dataframe, params and data config
    experiment_dir += name + '/'

    with open(experiment_dir + 'meta/model_params.json', 'r') as fp:
        model_params = json.load(fp)

    with open(experiment_dir + 'meta/data.json', 'r') as fp:
        data_config = json.load(fp)

    experiment_df = pd.read_csv(experiment_dir + 'meta/experiment.csv', index_col=0)

    # load the experiment object
    return SVGPExperiment(name, cluster_name, model_params=model_params, data_config=data_config, experiment_df=experiment_df)

def get_model_data_list_from_experiment(exp, experiment_dir='../run_model/experiments/'):
    """
    Given an experiment that has already been executed,
    return a list of updated model data objects.

    Parameters
    ___

    exp : Experiment
        Must have y_pred.npy for each result in experient_df.

    experiment_dir : str, optional
        Directory containing the experiment directory.

    Returns
    ___

    list
        List of ModelData objects with updated normalised_model_results_df.
    """

    model_data_list = []
    for index, row in exp.experiment_df.iterrows():
        # load model data from directory
        config_dir = experiment_dir + 'data/data{id}/'.format(id=row['data_id'])
        model_data = ModelData(config_dir=config_dir)

        # get the predictions from the model
        y_pred_fp = row['y_pred_fp']
        y_pred = np.load(y_pred_fp)

        # update model data with predictions
        pred_dict = model_data.get_pred_data_arrays(return_y=True)
        model_data.update_model_results_df(pred_dict, y_pred, {
            'fit_start_time':exp.data_config[row['data_id']]['pred_start_date']
        })

        # append model_data to list
        model_data_list.append(model_data)
    return model_data_list

def create_experiment_prefix(model_name, param_id, data_id):
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
        'tag': 'testing'
    }

def create_data_list(rolls, data_dir):
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

    for datatype in ['x_train', 'x_test', 'y_train', 'y_test']:
        for i in range(len(rolls)):
            data_config_list[i][datatype + '_fp'] = create_data_filepath(i, datatype, base_dir=data_dir)

    return data_config_list
    
def create_data_filepath(index, basename, base_dir='data/', extension='.npy'):
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

def numpy_files_exist(data_config):
    return (
        os.path.exists(data_config['x_train_fp'])
        and os.path.exists(data_config['y_train_fp'])
        and os.path.exists(data_config['x_test_fp'])
        and os.path.exists(data_config['y_test_fp'])
    )