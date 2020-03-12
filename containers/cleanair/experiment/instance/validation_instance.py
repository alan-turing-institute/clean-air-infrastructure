"""
Instance for validation that allows more flexibility such as reading/writing from files.
"""

import logging
import os
import pickle
from .runnable import RunnableInstance
from ...models import ModelData

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

    # DEFAULT_MODEL_NAME = "svgp"

    def __init__(self, **kwargs):
        self.y_test_pred = None
        self.y_train_pred = None

        # pass to super constructor
        super().__init__(**kwargs)

    def setup_model(self):
        if self.experiment_config["restore"]:
            raise NotImplementedError("Cannot yet restore model from file.")
        super().setup_model()

    def setup_data(self):
        if self.experiment_config["local_read"]:
            logging.info("Reading from local file.")
            self.model_data = ModelData(
                config_dir=self.experiment_config["config_dir"],
                secretfile=self.experiment_config["secretfile"],
            )
        else:
            super().setup_data()
        # save input data to file
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

    @classmethod
    def instance_from_id(cls, instance_id, experiment_config):
        """
        Given an id, return an initialised runnable instance.
        """
        # return instance from file
        if experiment_config["local_read"]:
            return None
        # return instance from DB
        return super().__class__.instance_from_id()
