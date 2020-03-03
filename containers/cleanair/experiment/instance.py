"""
Instances of models and data.
"""
import os
import json
import pickle
import hashlib
import logging
from datetime import datetime
import git
from ..models import ModelData, SVGP, MRDGP
from ..databases import DBWriter

class Instance():
    """
    An instance is one model trained and fitted on some data.
    """

    DEFAULT_DATA_CONFIG = {
        "train_start_date": "2020-01-29T00:00:00",
        "train_end_date": "2020-01-30T00:00:00",
        "pred_start_date": "2020-01-30T00:00:00",
        "pred_end_date": "2020-01-31T00:00:00",
        "include_satellite": True,
        "include_prediction_y": False,
        "train_sources": ["laqn"],
        "pred_sources": ["laqn"],
        "train_interest_points": "all",
        "train_satellite_interest_points": "all",
        "pred_interest_points": "all",
        "species": ["NO2"],
        "features": [
            "value_1000_total_a_road_length",
            "value_500_total_a_road_length",
            "value_500_total_a_road_primary_length",
            "value_500_total_b_road_length",
        ],
        "norm_by": "laqn",
        "model_type": "svgp",
        "tag": "production",
    }
    DEFAULT_MODEL_PARAMS = {
        "jitter": 1e-5,
        "likelihood_variance": 0.1,
        "minibatch_size": 100,
        "n_inducing_points": 200,
        "restore": False,
        "train": True,
        "model_state_fp": None,
        "maxiter": 100,
        "kernel": {"name": "mat32+linear", "variance": 0.1, "lengthscale": 0.1,},
    }
    MODELS = {
        'svgp': SVGP,
        'mr_dgp': MRDGP,
    }

    DEFAULT_MODEL_NAME = "svgp"

    DIGEST_SIZE = 20

    def __init__(self, **kwargs):
        # get the name of the model to run
        self.model_name = kwargs["model_name"] if "model_name" in kwargs else self.__class__.DEFAULT_MODEL_NAME

        # not a valid model
        if self.model_name not in self.__class__.MODELS:
            raise KeyError("{name} is not a valid model.".format(name=self.model_name))

        # set parameter id
        if "param_id" in kwargs:
            self.param_id = kwargs["param_id"]
        elif "model_params" in kwargs:
            self.param_id = self.hash_params(kwargs["model_params"])
        else:
            self.param_id = self.hash_params(self.__class__.DEFAULT_MODEL_PARAMS)

        # set data id
        if "data_id" in kwargs:
            self.data_id = kwargs["data_id"]
        elif "data_config" in kwargs:
            self.data_id = self.hash_data(kwargs["data_config"])
        else:
            self.data_id = self.hash_data(self.__class__.DEFAULT_DATA_CONFIG)

        # set cluster id
        self.cluster_id = kwargs["cluster_id"] if "cluster_id" in kwargs else "unassigned"

        # passing a tag
        self.tag = kwargs["tag"] if "tag" in kwargs else "unassigned"

        # creating the github hash
        self.hash = git.Repo(search_parent_directories=True).head.object.hexsha

        # get the instance id
        self.instance_id = self.hash_instance()

    def hash_instance(self):
        hash_string = self.model_name + str(self.param_id) + self.tag
        hash_string += str(self.data_id) + str(self.cluster_id)
        return Instance.hash_fn(hash_string)

    def hash_params(self, model_params):
        hash_string = json.dumps(model_params)
        return Instance.hash_fn(hash_string)

    def hash_data(self, data_config):
        hash_string = json.dumps(data_config)
        return Instance.hash_fn(hash_string)

    @staticmethod
    def hash_fn(hash_string):
        sha_fn = hashlib.sha256()
        sha_fn.digest_size = Instance.DIGEST_SIZE
        sha_fn.update(hash_string)
        return sha_fn.hexdigest()

class RunnableInstance(Instance):

    DEFAULT_EXPERIMENT_CONFIG = {
        "model_name": "svgp",
        "results_dir": "./",
        "model_dir": "./",
        "config_dir": "./",
        "local_read": False,
        "local_write": False,
        "predict_training": False,
        "predict_write": False,
        "no_db_write": False,
        "restore": False,
        "save_model_state": False,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # get experiment config (filepaths, write/read locally or DB, etc.)
        self.experiment_config = kwargs["experiment_config"] if "experiment_config" in kwargs else self.__class__.DEFAULT_EXPERIMENT_CONFIG

        # passing a model
        if "model" in kwargs:
            self.model = kwargs["model"]
            self.model_name = self.model.experiment_config["model_name"]

  
        # check if model params has been passed
        elif "model_params" in kwargs:
            # check for experiment config
            self.model = self.__class__.MODELS[self.model_name](
                model_params=kwargs["model_params"]
            )
        # if no params, try and read params from the db using param_id
        elif "param_id" in kwargs:
            raise NotImplementedError("Cannot yet read params from DB using 'param_id'.")

        # use default model params
        else:
            self.model = self.__class__.MODELS[self.model_name](
                model_params=self.__class__.DEFAULT_MODEL_PARAMS,
                experiment_config=self.experiment_config
            )

        # get model data from data id
        if "data_id" in kwargs:
            raise NotImplementedError("Cannot read data config from DB using data_id.")

        # get default model data
        elif "model_data" not in kwargs and "data_config" not in kwargs:
            data_config = self.__class__.DEFAULT_DATA_CONFIG
            data_config["tag"] = self.tag
            data_config["model_type"] = self.model_name

        # get model data from passed data config
        elif "model_data" not in kwargs and "data_config" in kwargs:
            data_config = kwargs["data_config"]

        # load model data object from kwargs
        if "model_data" in kwargs:
            self.model_data = kwargs["model_data"]
        # read from local directory
        elif "local_read" in self.experiment_config and self.experiment_config["local_read"]:
            self.model_data = ModelData(
                config_dir=self.experiment_config["config_dir"],
                secretfile=self.experiment_config["secretfile"],
            )
        # read using data config from DB
        else:
            self.model_data = ModelData(
                config=data_config,
                secretfile=self.experiment_config["secretfile"],
            )

        # reset the ids
        self.data_id = self.hash_data(self.model_data.config)
        self.param_id = self.hash_params(self.model.model_params)
        self.instance_id = self.hash_instance()

    def run(self):
        """
        Run the instance: train and predict a model.
        """
        # save input data to file
        if self.experiment_config["local_write"]:
            self.model_data.save_config_state(self.experiment_config["config_dir"])

        # get the training and test dictionaries
        training_data_dict = self.model_data.get_training_data_arrays(dropna=False)
        predict_data_dict = self.model_data.get_pred_data_arrays(dropna=False)
        x_train = training_data_dict["X"]
        y_train = training_data_dict["Y"]
        x_test = predict_data_dict["X"]

        # Fit the model
        logging.info(
            "Training the model for %s iterations.", self.model.model_params["maxiter"]
        )
        fit_start_time = datetime.now()
        self.model.fit(x_train, y_train)

        # Do prediction
        y_test_pred = self.model.predict(x_test)
        if self.experiment_config["predict_training"]:
            x_train_pred = x_train.copy()
            if "satellite" in x_train:  # don't predict at satellite
                x_train_pred.pop("satellite")
            y_train_pred = self.model.predict(x_train_pred)

        # Internally update the model results in the ModelData object
        self.model_data.update_test_df_with_preds(y_test_pred, fit_start_time)

        # Write the model results to the database
        if not self.experiment_config["no_db_write"]:
            # see issue 103: generalise for multiple pollutants
            self.model_data.normalised_pred_data_df[
                "predict_mean"
            ] = self.model_data.normalised_pred_data_df["NO2_mean"]
            self.model_data.normalised_pred_data_df[
                "predict_var"
            ] = self.model_data.normalised_pred_data_df["NO2_var"]
            self.model_data.update_remote_tables()

        # Write the model results to file
        if self.experiment_config["predict_write"]:
            self.write_predictions_to_file(y_test_pred, "test_pred.pickle")
            if self.experiment_config["predict_training"]:
                self.write_predictions_to_file(y_train_pred, "train_pred.pickle")

    def write_predictions_to_file(self, y_pred, filename):
        """Write a prediction dict to pickle."""
        pred_filepath = os.path.join(self.experiment_config["results_dir"], filename)
        with open(pred_filepath, "wb") as handle:
            pickle.dump(y_pred, handle)

class WritableInstance(Instance, DBWriter):
    """
    Adds functionality for reading and writing to the DB.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def update_table(self):
        """
        Update the instance table and (if necessary) data and model tables.
        """
        raise NotImplementedError()

class ProductionInstance(RunnableInstance):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
class LaqnTestInstance(RunnableInstance):
    """
    A quick test only on LAQN data that trains for 1 days and predicts for 1 day.
    """

    DEFAULT_DATA_CONFIG = {
        "train_start_date": "2020-01-29T00:00:00",
        "train_end_date": "2020-01-30T00:00:00",
        "pred_start_date": "2020-01-30T00:00:00",
        "pred_end_date": "2020-01-31T00:00:00",
        "include_satellite": False,
        "include_prediction_y": False,
        "train_sources": ["laqn"],
        "pred_sources": ["laqn"],
        "train_interest_points": "all",
        "train_satellite_interest_points": "all",
        "pred_interest_points": "all",
        "species": ["NO2"],
        "features": [
            "value_1000_total_a_road_length",
            "value_500_total_a_road_length",
            "value_500_total_a_road_primary_length",
            "value_500_total_b_road_length",
        ],
        "norm_by": "laqn",
        "model_type": "svgp",
        "tag": "test",
    }

    DEFAULT_MODEL_PARAMS = {
        "jitter": 1e-5,
        "likelihood_variance": 0.1,
        "minibatch_size": 100,
        "n_inducing_points": 200,
        "restore": False,
        "train": True,
        "model_state_fp": None,
        "maxiter": 1,
        "kernel": {"name": "mat32+linear", "variance": 0.1, "lengthscale": 0.1,},
    }

    def __init__(self, **kwargs):
        """
        Setup a quick test instance.

        Parameters
        ___

        secretfile : str
            Filepath to the secretfile.

        config_dir : str, optional
            Filepath to the directory of data.
        """
        # Get the model data
        super().__init__(
            model_data=ModelData(config=LaqnTestInstance.DEFAULT_DATA_CONFIG, **kwargs),
            model_name="svgp",
            tag="test",
            model=SVGP(
                model_params=LaqnTestInstance.DEFAULT_MODEL_PARAMS,
                tasks=self.model_data.config["species"],
            ),
            cluster_id="laptop",
            **kwargs,
        )
