"""
The base class for experiments.
"""

import os
import sys
import json
import pickle
from abc import ABC, abstractmethod
import pandas as pd
import pathlib
import itertools

from .. import metrics
from .. import util
from ..cluster import *

#requires cleanair
sys.path.append("../containers/")
sys.path.append("../../containers/")

try:
    from cleanair.models import ModelData
except ImportError:
    print('WARNING: Could not import ModelData')

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
        self.model_data_list = kwargs['model_data_list'] if 'model_data_list' in kwargs else []
        self.experiments_directory = kwargs['directory'] if 'directory' in kwargs else 'experiment_data/'
        self.home_directory = kwargs['home_directory'] if 'home_directory' in kwargs else '~'
        self.secretfile = kwargs['secretfile'] if 'secretfile' in kwargs else '../terraform/.secrets/db_secrets.json'

        self.experiments_directory = util.ensure_last_backslash(self.experiments_directory)
        self.home_directory = util.ensure_last_backslash(self.home_directory)

        self.available_clusters = {
            'laptop': Laptop,
            'pearl': Pearl
        }

    @abstractmethod
    def get_default_model_params(self):
        """
        Get the default parameters of the model for this experiment.
        """

    @abstractmethod
    def get_default_data_config(self, **kwargs):
        """
        Get the default data configurations for this experiment.
        """

    def get_default_experiment_df(self):
        """
        Create a dataframe where each line is one run/result of an experiment.
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

        experiment_df['results_dir'] = pd.Series([
            util.create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) for r in experiment_df.itertuples()])

        experiment_df['model_state_fp'] = pd.Series([
            self.experiments_directory + '{name}/models/restore/m_{model_name}_'.format(name=self.name, model_name=r.model_name) + util.create_experiment_prefix(
                r.model_name, r.param_id, r.data_id
            ) + '.model' for r in experiment_df.itertuples()])

        return experiment_df

    def setup(self, force_redownload=False):
        """
        Given an experiment create directories, data and files.
        """
        # create directories for experiment data
        experiment_dir = self.experiments_directory + self.name + '/'
        self.__create_experiment_data_directories()

        # store a list of ModelData objects to validate over
        self.model_data_list = []

        # create ModelData objects for each roll
        for index, row in self.experiment_df.iterrows():
            data_id = row['data_id']
            data_config = self.data_config[data_id]

            # If the numpy files do not exist locally
            if force_redownload or not util.pickle_files_exist(data_config):
                # make new directory for data
                data_dir_path = experiment_dir + 'data/data{id}'.format(id=data_id)
                pathlib.Path(data_dir_path).mkdir(exist_ok=True)

                # Get the model data and append to list
                model_data = ModelData(config=data_config, secretfile=self.secretfile)
                self.model_data_list.append(model_data)

                # save config status of the model data object to the data directory
                model_data.save_config_state(data_dir_path)

                # get the training and testing dicts indexed by source
                training_dict = model_data.get_training_dict()
                test_dict = model_data.get_test_dict()

                # write to a pickle
                with open(data_config['train_fp'], 'wb') as handle:
                    pickle.dump(training_dict, handle)
                with open(data_config['test_fp'], 'wb') as handle:
                    pickle.dump(test_dict, handle)

        # load and write model data objects to files
        self.save_meta_files()

    def save_meta_files(self):
        """
        Save the experiment_df, model_params and data_config to csv and json.
        """
        exp_dir = self.experiments_directory + self.name + '/'

        # save experiment dataframe to csv
        self.experiment_df.to_csv(exp_dir + 'meta/experiment.csv')

        # save data and params configs to json
        with open(exp_dir + 'meta/data.json', 'w') as fp:
            json.dump(self.data_config, fp, indent=4)

        with open(exp_dir + 'meta/model_params.json', 'w') as fp:
            json.dump(self.model_params, fp, indent=4)

    def __create_experiment_data_directories(self):
        """
        Create directories if they don't exist.
        """
        exp_dir = self.experiments_directory + self.name + '/'
        pathlib.Path(self.experiments_directory).mkdir(exist_ok=True)
        pathlib.Path(exp_dir).mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'results').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'data').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'meta').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'models').mkdir(exist_ok=True)
        pathlib.Path(exp_dir + 'models/restore').mkdir(exist_ok=True)

    def __create_experiment_results_directories(self):
        """
        Create directories to store results in if they don't already exist.
        """
        for row in self.experiment_df.itertuples():
            pathlib.Path(os.path.join(self.experiments_directory, self.name, 'results', row.results_dir)).mkdir(exist_ok=True)

    def __get_cluster_obj(self):
        """
        Load cluster object from cluster object and check it exists.
        """
        if self.cluster in self.available_clusters:
            return self.available_clusters[self.cluster]
        else:
            raise ValueError("Cluster does not exist: ",self.cluster)

    def run(self):
        """
        Run the experiment.
        """
        # before running any models, create the results directories
        self.__create_experiment_results_directories()
        experiment_df = self.get_default_experiment_df()

        cluster_run_params = []

        for model in self.models:
            model_experiment_df = experiment_df[experiment_df['model_name'] == model]
            for index, row in self.experiment_df.iterrows():
                exp_dict = {
                    'filename': model,
                    'data_id': row['data_id'],
                    'param_id': row['param_id']
                }
                cluster_run_params.append(exp_dict)

        input_format_fn = lambda config: ' {param_id} {data_id}'.format(data_id=config['data_id'], param_id=config['param_id'])

        cluster = self.__get_cluster_obj()(
            experiment_name=self.name,
            cluster_config={},
            experiment_configs=cluster_run_params,
            input_format_fn=input_format_fn,
            cluster_tmp_fp=self.experiments_directory+'cluster',
            experiment_fp=self.experiments_directory,
            home_directory_fp=self.home_directory,
        )
        cluster.setup()

        cluster.run()


    def check_status(self):
        """
        Check the status of an experiment on a cluster.
        """
        pass

    def update_model_data_list(self, update_test=True, update_train=False):
        """
        Update the model data list from local files.

        Parameters
        ___

        update_test : bool, optional
            The normalised_pred_data_df for each model data object is updated with new predictions.

        update_train : bool, optional
            The normalised_training_data_df for each model data object is updated with new predictions.
            There must exist a `train_pred.pickle` file in the results directory for each result.
        """
        model_data_list = []
        for index, row in self.experiment_df.iterrows():
            # load model data from directory
            config_dir = self.experiments_directory + '{name}/data/data{id}/'.format(name=self.name, id=row['data_id'])
            model_data = ModelData(config_dir=config_dir, secretfile=self.secretfile)

            # get the predictions from the model for testing data
            results_dir = row['results_dir']
            if update_test:
                test_pred_fp = '{dir}{name}/results/{id}/test_pred.pickle'.format(dir=self.experiments_directory, name=self.name, id=results_dir)
                with open(test_pred_fp, 'rb') as handle:
                    print()
                    print(test_pred_fp)
                    print()
                    test_pred_dict = pickle.load(handle)

                # update model data with predictions
                model_data.update_testing_df_with_preds(test_pred_dict)

            if update_train:
                # try to update the predictions for the training set
                try:
                    train_pred_fp = '{dir}{name}/results/{id}/train_pred.pickle'.format(dir=self.experiments_directory, name=self.name, id=results_dir)
                    with open(train_pred_fp, 'rb') as handle:
                        train_pred_dict = pickle.load(handle)
                    model_data.update_training_df_with_preds(train_pred_dict)
                except FileNotFoundError:
                    print("WARNING: no predictions on training set.")

            # append model_data to list
            model_data_list.append(model_data)
        self.model_data_list = model_data_list

    def evaluate(self, metric_methods, evaluate_testing=True, evaluate_training=False):
        """
        Measure the metrics of an experiment.

        Parameters
        ___

        metric_methods : dict
            A dictionary where keys are the name of a metric and values
            are a function that takes two numpy arrays of the same shape.

        evaluate_testing : bool, optional
            If true, this function will evaluate the predictions made
            on the testing set of data.    

        evaluate_training : bool, optional
            If true, this function will evaluate the predictions made
            on the training set of data.

        Returns
        ___

        sensor_scores_df : pd.DataFrame
            For every instance of the experiment, we calculate the score
            of a sensor over the whole prediction time period.

        temporal_scores_df : pd.DataFrame
            For every instance of an experiment, we calculate the scores
            over all sensors given a slice in time.

        Notes
        ___
        
        We assume that the `model_data_list` of an experiment
        has already been updated with the predictions.
        We assume that all instances of an experiment predict on the same
        species of pollutant.

        Examples
        ___
            >>> xp.update_model_data_list() # remember to update predictions
            >>> metric_methods = get_metric_methods()
            >>> scores_df = xp.evaluate(metric_methods)
        """
        # the basic cols that every scoring dataframe should have
        cols = [
            'experiment_name', 'instance_id', 'cluster_name', 'param_id',
            'data_id', 'training_set', 'testing_set'
        ]
        sensor_cols = cols.copy()
        temporal_cols = cols.copy()
        sensor_cols.append('point_id')
        temporal_cols.append('measurement_start_utc')

        # add columns that will measure the metrics for each pollutant
        list_of_species = self.model_data_list[0].config['species'].copy()
        print('List of species:', list_of_species)
        metric_cols = [
            '{species}_{mtc}'.format(species=s, mtc=m)
            for s, m in itertools.product(list_of_species, metric_methods.keys())
        ]
        print('Metric cols:', metric_cols)
        sensor_cols.extend(metric_cols)
        temporal_cols.extend(metric_cols)

        # create dataframes for collecting scores over space and time
        sensor_scores_df = pd.DataFrame(columns=sensor_cols)
        temporal_scores_df = pd.DataFrame(columns=temporal_cols)

        # sensor_scores_df = pd.DataFrame(columns=)
        for index, row in self.experiment_df.iterrows():
            model_data = self.model_data_list[index]

            # get prediction and testing column names
            pred_cols = ['{s}_mean'.format(s=spc) for spc in model_data.config['species']]
            test_cols = model_data.config['species'].copy()

            # evaluate the metrics at sensors and in time
            instance_sensor_scores_df, instance_temporal_scores_df = metrics.evaluate_model_data(
                model_data, metric_methods,
                evaluate_training=evaluate_training,
                evaluate_testing=evaluate_testing,
                pred_cols=pred_cols,
                test_cols=test_cols,
                experiment_name=self.name,
                instance_id=index,
                cluster_name=self.cluster,
                param_id=row['param_id'],
                data_id=row['data_id']
            )

            # append to the bigger dataframes
            sensor_scores_df = sensor_scores_df.append(instance_sensor_scores_df, ignore_index=True)
            temporal_scores_df = temporal_scores_df.append(instance_temporal_scores_df, ignore_index=True)

        return sensor_scores_df, temporal_scores_df
