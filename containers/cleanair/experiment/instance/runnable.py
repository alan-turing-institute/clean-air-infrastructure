"""
An instance that can be executed using the run() method.
"""

import os
import pickle
import logging
from datetime import datetime
from .instance import Instance
from ...models import ModelData


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
            print(self.model.experiment_config)
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

        # get data_config from data id
        if "data_id" in kwargs:
            raise NotImplementedError("Cannot read data config from DB using data_id.")
        # get default data config
        elif "model_data" not in kwargs and "data_config" not in kwargs:
            data_config = self.__class__.DEFAULT_DATA_CONFIG
            data_config["tag"] = self.tag

        # get passed data config
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
        # read modeldata using data config
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

        print("Y pred:", y_test_pred)

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