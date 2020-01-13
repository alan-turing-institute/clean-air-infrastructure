from abc import ABC, abstractmethod
import pandas as pd
import itertools

# validation modules
import temporal

class Experiment(ABC):

    def __init__(self, experiment_name, model_name, cluster_name, **kwargs):
        """
        An abstract experiment class.

        Parameters
        ___

        experiment_name : str
            Name that identifies the experiment.

        model_name : str
            String identifying the model ran in the experiment.

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
        self.model_name = model_name
        self.cluster = cluster_name
        self.model_params = kwargs['model_params'] if 'model_params' in kwargs else []
        self.data_config = kwargs['data_config'] if 'data_config' in kwargs else []
        self.experiment_df = kwargs['experiment_df'] if 'experiment_df' in kwargs else pd.DataFrame()

    @abstractmethod
    def get_default_model_params(self):
        """
        Get the default parameters of the model for this experiment.
        """
        pass

    @abstractmethod
    def get_default_data_config(self):
        """
        Get the default data configurations for this experiment.
        """
        pass

    @abstractmethod
    def get_default_experiment_df(self):
        """
        Get all the default experiment configurations.
        """
        pass

class SVGPExperiment(Experiment):

    def __init__(self, experiment_name, cluster_name, **kwargs):
        super().__init__(experiment_name, 'svgp', cluster_name, **kwargs)
        if 'model_params' not in kwargs:
            self.model_params = self.get_default_model_params()
        if 'data_config' not in kwargs:
            self.data_config = self.get_default_data_config()
        if 'experiment_df' not in kwargs:
            self.experiment_df = self.get_default_experiment_df()        

    def get_default_model_params(self):
        return create_params_list(
            lengthscale=[0.1],
            variance=[0.1],
            minibatch_size=[100],
            n_inducing_point=[3000]
        )

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

    def get_default_experiment_df(self):
        experiment_configs = {
            'model_name':[self.model_name],
            'param_id':[item['id'] for item in self.model_params],
            'data_id':[item['id'] for item in self.data_config],
            'cluster':[self.cluster]
        }
        list_of_configs = [values for key, values in experiment_configs.items()]
        params_configs = list(itertools.product(*list_of_configs))
        experiment_df = pd.DataFrame(params_configs, columns=experiment_configs.keys())

        experiment_df['y_pred_fp'] = pd.Series([create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + 'y_pred.npy' for r in experiment_df.itertuples()])

        experiment_df['y_var_fp'] = pd.Series([create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + 'y_var.npy' for r in experiment_df.itertuples()])

        experiment_df['model_state_fp'] = pd.Series([create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + '.model' for r in experiment_df.itertuples()])

        return experiment_df

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
    return base_dir + 'data' + str(index) + '_' + basename + extension

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
