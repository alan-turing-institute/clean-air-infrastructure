"""
Instance for validation that allows more flexibility such as reading/writing from files.
"""

import logging
import os
import json
import pickle
from .runnable import RunnableInstance
from ..models import ModelData

class ValidationInstance(RunnableInstance):

    DEFAULT_EXPERIMENT_CONFIG = dict(
        RunnableInstance.DEFAULT_EXPERIMENT_CONFIG.copy(),
        results_dir="./",
        model_dir="./",
        config_dir="./",
        local_read=False,
        local_write=False,
        predict_training=False,
        predict_write=False,
        no_db_write=False,
        restore=False,
        save_model_state=False,
    )

    DEFAULT_MODEL_PARAMS = {
        "jitter": 1e-5,
        "likelihood_variance": 0.1,
        "minibatch_size": 100,
        "n_inducing_points": 200,
        "maxiter": 1,
        "kernel": {"name": "mat32+linear", "variance": 0.1, "lengthscale": 0.1,},
    }

    DEFAULT_DATA_CONFIG = dict(
        RunnableInstance.DEFAULT_DATA_CONFIG.copy(),    # use super class dict
        include_prediction_y=True,
        include_satellite=True,
    )

    DEFAULT_MODEL_NAME = "svgp"

    def __init__(self, **kwargs):
        self.y_test_pred = None
        self.y_train_pred = None

        # pass to super constructor
        super().__init__(**kwargs)

    def setup_model(self):
        if self.experiment_config["restore"]:
            raise NotImplementedError("Cannot yet restore model from file.")
        super().setup_model()
        if self.experiment_config["write_model_params"]:
            model_params_fp = os.path.join(self.experiment_config["model_dir"], "model_params.json")
            logging.info("Writing model parameters to json file.")
            with open(model_params_fp, "w") as json_file:
                json.dump(self.model_params, json_file)

    def load_data(self):
        if self.experiment_config["local_read"]:
            logging.info("Reading from local file.")
            self.model_data = ModelData(
                config_dir=self.experiment_config["config_dir"],
                secretfile=self.experiment_config["secretfile"],
            )
        else:
            super().load_data()
        # save input data and model params to file
        if self.experiment_config["local_write"]:
            self.model_data.save_config_state(self.experiment_config["config_dir"])

    def save_results(self):
        if self.experiment_config["predict_write"]:
            logging.info("Writing predictions to file.")
            self.write_predictions_to_file(self.y_test_pred, "test_pred.pickle")
            if self.experiment_config["predict_training"]:
                self.write_predictions_to_file(self.y_train_pred, "train_pred.pickle")
        elif not self.experiment_config["no_db_write"]:
            # ToDo: remove exception
            super().save_results()
        else:
            logging.warning("Did not write predictions.")

    def run_prediction(self):
        logging.info("Starting prediction.")
        y_test_pred = super().run_prediction()

        if self.experiment_config["predict_training"]:
            training_data_dict = self.model_data.get_training_data_arrays(dropna=False)
            x_train = training_data_dict["X"]
            x_train_pred = x_train.copy()
            if "satellite" in x_train:  # don't predict at satellite
                x_train_pred.pop("satellite")
            self.y_train_pred = self.model.predict(x_train_pred)
            raise NotImplementedError("Not sure how to get the training data back again?")

        return y_test_pred

    def write_predictions_to_file(self, y_pred, filename):
        """Write a prediction dict to pickle."""
        pred_filepath = os.path.join(self.experiment_config["results_dir"], filename)
        with open(pred_filepath, "wb") as handle:
            pickle.dump(y_pred, handle)

    def __get_results_df(self):
        """
        Get a subset of normalised_pred_data_df with the predictions in.
        """
        record_cols = [
            "instance_id",
            "point_id",
            "measurement_start_utc",
            "NO2_mean",
            "NO2_var",
        ]
        return self.model_data.normalised_pred_data_df[record_cols]

    def load_results(self, training_set=False, test_set=True):
        """
        Load the predictions, either from a file or from the DB.

        Parameters
        ___

        filename : str
            E.g. test_pred.pickle, train_pred.pickle.
            Not the full filepath! The filepath is given by experiment_config.
        """
        if training_set:
            raise NotImplementedError("Cannot yet load results for the training set.")

        if test_set and self.experiment_config["predict_read_local"]:
            # load the prediction pickle files and return a results df
            filepath = os.path.join(self.experiment_config["results_dir"], "test_pred.pickle")
            with open(filepath, "rb") as handle:
                y_pred = pickle.load(handle)
            self.update_results(y_pred)
            return self.__get_results_df()
        # else read the results from the DB using super class.
        return super().load_results(training_set=training_set, test_set=test_set)

    def load_model_params(self, **kwargs):
        """
        Loads the model params from the DB or from a file
        (if read_model_params is True in experiment_config).

        Parameters
        ___

        model_name : str, optional
            Name of the model. Must be supplied if reading from DB.

        param_id : str, optional
            Hashed id of model_params. Must be supplied if reading from DB.

        filename : str, optional
            Name of the json file containing model params.

        Returns
        ___

        model_params : dict
            Dictionary of model parameters.
        """
        if self.experiment_config["read_model_params"]:
            filename = kwargs.pop("filename", "model_params.json")
            filepath = os.path.join(self.experiment_config["model_dir"], filename)
            with open(filepath, "w") as json_file:
                return json.load(json_file)
        return super().load_model_params(**kwargs)

    @classmethod
    def instance_from_id(cls, instance_id, experiment_config, **kwargs):
        """
        Given an id, return an initialised runnable instance.

        Parameters
        ___

        instance_id : str
            Unique id for the instance that is used to load the instance.

        experiment_config : dict
            How the instance will be loaded, e.g. from file? from DB?.

        Other Parameters
        ___

        kwargs : dict, optional
            See __init__.
            If loading instance from file then should pass through cluster_id,
            git_hash, fit_start_time and tag.
        """
        # return instance from file
        if experiment_config["local_read"]:
            instance = cls(
                instance_id=instance_id,
                experiment_config=experiment_config,
                **kwargs,
            )
            # load the data config from file
            data_config_fp = os.path.join(experiment_config["config_dir"], "config.json")
            with open(data_config_fp, "r") as json_file:
                instance.data_config = json.load(json_file)

            # get model parameters from file
            model_params_fp = os.path.join(experiment_config["model_dir"], "model_params.json")
            with open(model_params_fp, "r") as json_file:
                instance.model_params = json.load(json_file)

            return instance
        # return instance from DB
        return RunnableInstance.instance_from_id(instance_id, experiment_config)
