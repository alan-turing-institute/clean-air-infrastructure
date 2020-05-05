"""
A base class for cleanair parsers.
"""
import json
import argparse
import datetime
from ..instance import RunnableInstance
from ..mixins import SecretFileParserMixin, VerbosityMixin
from ..timestamps import as_datetime


class BaseModelParser(SecretFileParserMixin, VerbosityMixin, argparse.ArgumentParser):
    """
    Parser for CleanAir model entrypoints.
    """

    MODEL_ARGS = []
    EXPERIMENT_ARGS = ["local_read", "config_dir", "secretfile"]
    DATA_ARGS = ["trainend", "trainhours", "predstart", "predhours", "predict_training", "include_prediction_y"]

    def __init__(self, config_path="../../terraform/.secrets/config.json", **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path
        # essential arguments
        self.add_argument(
            "-c",
            "--cleanair_config",
            action="store_true",
            default=False,
            help="Use your config.json settings in the .secrets directory.",
        )
        self.add_argument(
            "-m",
            "--model_name",
            type=str,
            default=RunnableInstance.DEFAULT_MODEL_NAME,
            help="Model to run.",
        )
        self.add_argument(
            "-t",
            "--tag",
            type=str,
            default="test",
            help="Tag to identify the model fit.",
        )
        self.add_argument(
            "-cluster_id",
            type=str,
            default="azure",
            help="Name of machine/cluster the model is run on.",
        )
        self.add_argument(
            "-d",
            "--config_dir",
            default=RunnableInstance.DEFAULT_EXPERIMENT_CONFIG["config_dir"],
            help="Filepath to directory to store model and data.",
        )
        # whether to read and write from the database or locally
        self.add_argument(
            "--local-read",
            action="store_true",
            default=False,
            help="Read local training/test data from config_dir.",
        )
        # optional params for data
        self.add_argument(
            "-y",
            "--include_prediction_y",
            action="store_true",
            default=False,
            help="Include pollutant data in the test dataset.",
        )
        self.add_argument(
            "-p",
            "--predict-training",
            action="store_true",
            default=False,
            help="Predict on the training set.",
        )
        # datetimes for training and prediction
        self.add_argument(
            "--trainend",
            type=str,
            default=RunnableInstance.DEFAULT_DATA_CONFIG["train_end_date"],
            help="The last datetime (YYYY-MM-DD HH:MM:SS) to get model data for training.",
        )
        self.add_argument(
            "--trainhours",
            type=int,
            default=48,
            help="The number of hours to get training data for.",
        )
        self.add_argument(
            "--predstart",
            type=str,
            default=RunnableInstance.DEFAULT_DATA_CONFIG["pred_start_date"],
            help="The first datetime (YYYY-MM-DD HH:MM:SS) to get model data for prediction.",
        )
        self.add_argument(
            "--predhours",
            type=int,
            default=48,
            help="The number of hours to predict for",
        )

        self.data_args = dict()
        self.experiment_args = dict()
        self.model_args = dict()

    def parse_all(self):
        """
        If the -c flag is passed, then load the config.json file
        and overwrite any fields that are passed in kwargs.
        """
        args = self.parse_args()
        kwargs = vars(args)

        if kwargs.pop("cleanair_config"):
            # load custom config and overwrite arguments passed
            with open(self.config_path, "r") as filepath:
                config = json.load(filepath)
            for key, value in config.items():
                if key in kwargs:
                    kwargs[key] = value

        # get model params
        self.model_args = {
            key: kwargs.pop(key) for key in self.__class__.MODEL_ARGS
        }
        # get data params
        train_end_date = as_datetime(kwargs.pop("trainend"))
        train_start_date = train_end_date - datetime.timedelta(
            hours=kwargs.pop("trainhours")
        )
        pred_start_date = as_datetime(kwargs.pop("predstart"))
        pred_end_date = pred_start_date + datetime.timedelta(
            hours=kwargs.pop("predhours")
        )
        include_prediction_y = kwargs.pop("include_prediction_y", False)
        self.data_args = {
            "train_start_date": train_start_date,
            "train_end_date": train_end_date,
            "pred_start_date": pred_start_date,
            "pred_end_date": pred_end_date,
            "include_prediction_y": include_prediction_y,
        }
        # get experiment params
        self.experiment_args = {
            key: kwargs.pop(key) for key in self.__class__.EXPERIMENT_ARGS
        }
        return kwargs

    def save_config(self):
        """
        Save the key and values of the parser to a json file.
        """
        kwargs = vars(self.parse_args())
        with open(self.config_path, "w") as filepath:
            json.dump(kwargs, filepath)
