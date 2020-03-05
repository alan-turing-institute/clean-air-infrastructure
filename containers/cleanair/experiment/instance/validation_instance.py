"""
Instance for validation that allows more flexibility such as reading/writing from files.
"""

import os
import pickle
import logging
from .runnable import RunnableInstance

class ValidationInstance(RunnableInstance):

    DEFAULT_EXPERIMENT_CONFIG = {
        "model_name": "mr_dgp",
        "secretfile": "../../terraform/.secrets/db_secrets.json",
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
        self.y_test_pred = None
        self.y_train_pred = None

        # get default experiment config
        experiment_config = self.__class__.DEFAULT_EXPERIMENT_CONFIG.copy()

        # update with passed config
        experiment_config.update(kwargs.pop("experiment_config", {}))

        # pass to super constructor
        super().__init__(experiment_config=experiment_config, **kwargs)

    def setup_model(self):
        if self.experiment_config["restore"]:
            raise NotImplementedError("Cannot yet restore model from file.")
        super().setup_model()

    def setup_data(self):
        if self.experiment_config["local_read"]:
            raise NotImplementedError("Cannot yet load data from files.")
        super().setup_data()
        # save input data to file
        if self.experiment_config["local_write"]:
            self.model_data.save_config_state(self.experiment_config["config_dir"])

    def save_results(self):
        if self.experiment_config["predict_write"]:
            self.write_predictions_to_file(self.y_test_pred, "test_pred.pickle")
            if self.experiment_config["predict_training"]:
                self.write_predictions_to_file(self.y_train_pred, "train_pred.pickle")
        elif not self.experiment_config["no_db_write"]:
            super().save_results()
        else:
            logging.warning("Did not write predictions.")

    def run_prediction(self):
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
