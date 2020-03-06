"""
An instance that can be executed using the run() method.
"""

import logging
import os
import json
import pickle
from datetime import datetime
from .instance import Instance
from ...models import ModelData

class RunnableInstance(Instance):

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
        "tag": "validation",
    }
    
    def __init__(self, **kwargs):
        """
        A runnable instance is determined by its data, model and experiment settings.

        Parameters
        ___

        data_config : dict, optional
            Settings for data.

        experiment_config : dict, optional
            Settings that do not affect the model outcome, e.g. filepaths.

        model_params : dict, optional
            The parameters to run the model with.

        Other Parameters
        ___

        kwargs : dict, optional
            See `Instance`.
        """
        super().__init__(**kwargs)

        xp_config = kwargs.get("experiment_config", None)
        model_params = kwargs.get("model_params", None)
        data_config = kwargs.get("data_config", None)

        # get experiment config (filepaths, write/read locally or DB, etc.)
        if xp_config:
            self.experiment_config = xp_config
        else:
            raise AttributeError("You must pass an experiment config.")

        logging.debug("Experiment config: %s", json.dumps(self.experiment_config, indent=4))

        # check if model params has been passed
        if model_params:
            self._model_params = model_params
            self.param_id = RunnableInstance.__hash_dict(model_params)
        elif kwargs.get("param_id"):
            raise NotImplementedError("Cannot yet load parameters from DB.")
        
        # get data config dict
        if data_config:
            self._data_config = data_config
            self.data_id = RunnableInstance.__hash_dict(data_config)
        elif kwargs.get("data_id"):     # check if data id has been passed
            raise NotImplementedError("Cannot yet read data id from DB.")
        else:
            raise NotImplementedError("You must pass either a data_config or data_id.")
        
        # make model and data
        self.model = None
        self.model_data = None

    @property
    def model_params(self):
        return self._model_params

    @model_params.setter
    def model_params(self, value):
        self._model_params = value
        # update param id
        self.param_id = RunnableInstance.__hash_dict(value)

    @property
    def data_config(self):
        return self._data_config
    
    @data_config.setter
    def data_config(self, value):
        self._data_config = value
        self.data_id = RunnableInstance.__hash_dict(value)

    @staticmethod
    def __hash_dict(value):
        hash_string = json.dumps(value)
        return Instance.hash_fn(hash_string)

    def load_model_params(self, **kwargs):
        """
        Load model parameters from DB or use defaults.
        """

    def setup_model(self):
        """
        From the model name and params, set up a model.
        """
        self.model = self.__class__.MODELS[self.model_name](
            experiment_config=self.experiment_config,
            model_params=self.model_params,
            tasks=self.data_config["species"],
        )

    def setup_data(self):
        """
        From the data and experiment config, setup a model data object.
        """
        self.model_data = ModelData(
            config=self.data_config,
            secretfile=self.experiment_config["secretfile"],
        )

    def run_model_fitting(self):
        """
        Train the model on data.
        """
        training_data_dict = self.model_data.get_training_data_arrays(dropna=False)
        x_train = training_data_dict["X"]
        y_train = training_data_dict["Y"]

        self.fit_start_time = datetime.now()
        logging.info(
            "Training the model for %s iterations.", self.model_params["maxiter"]
        )
        logging.info("Training started.")
        self.model.fit(x_train, y_train)
        logging.info("Training ended.")

    def run_prediction(self):
        """
        Predict on the test set using a trained model.
        """
        logging.info("Prediction started.")
        predict_data_dict = self.model_data.get_pred_data_arrays(dropna=False)
        x_test = predict_data_dict["X"]
        y_pred = self.model.predict(x_test)
        logging.info("Prediction finished.")
        return y_pred

    def update_results(self, y_pred):
        """
        From the predictions, update a DB or file with the results.
        """
        self.model_data.update_test_df_with_preds(y_pred, self.fit_start_time)

    def save_results(self):
        """
        Upload instance, params and results to the database.
        """
        self.model_data.normalised_pred_data_df[
            "predict_mean"
        ] = self.model_data.normalised_pred_data_df["NO2_mean"]
        self.model_data.normalised_pred_data_df[
            "predict_var"
        ] = self.model_data.normalised_pred_data_df["NO2_var"]
        self.model_data.update_remote_tables()

    def run(self):
        """
        Setup, train, predict and update all in one step.
        """
        self.setup_model()
        self.setup_data()
        self.run_model_fitting()
        y_pred = self.run_prediction()
        self.update_results(y_pred)
        self.save_results()
