"""
A base class for cleanair parsers.
"""

import json
import argparse
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from ..experiment import RunnableInstance

class CleanAirParser(argparse.ArgumentParser):
    """
    The base cleanair entrypoint parser.
    """

    MODEL_ARGS = []
    EXPERIMENT_ARGS = ["local_read", "config_dir", "secretfile"]
    DATA_ARGS = ["trainend", "trainhours", "predstart", "predhours", "predict_training", "include_prediction_y"]
    MISC_ARGS = ["model_name", "tag", "verbose"]

    def __init__(self, config_path="../../terraform/.secrets/config.json", **kwargs):
        super().__init__(**kwargs)
        self.config_path = config_path
        # essential arguments
        self.add_argument(
            "-c",
            "--cleanair_config",
            action="store_true",
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
            "-s",
            "--secretfile",
            default=RunnableInstance.DEFAULT_EXPERIMENT_CONFIG["secretfile"],
            help="File with connection secrets.",
        )
        self.add_argument(
            "-d",
            "--config_dir",
            default=RunnableInstance.DEFAULT_EXPERIMENT_CONFIG["config_dir"],
            help="Filepath to directory to store model and data.",
        )
        self.add_argument("-v", "--verbose", action="count", default=0)
        # whether to read and write from the database or locally
        self.add_argument(
            "-local_read",
            action="store_true",
            help="Read local training/test data from config_dir.",
        )
        # optional params
        self.add_argument(
            "-y",
            "--include_prediction_y",
            action="store_true",
            help="Include pollutant data in the test dataset.",
        )
        self.add_argument(
            "-p",
            "--predict_training",
            action="store_true",
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

    def parse_all(self):
        args = super().parse_args()
        kwargs = vars(args)

        # get kwargs from json file
        if kwargs.pop("cleanair_config"):
            # load custom config and overwrite arguments passed
            with open(self.config_path, "r") as filepath:
                config = json.load(filepath)
            for key, value in config.items():
                if key in kwargs:
                    kwargs[key] = value

        # get misc kwargs
        misc = {key: kwargs.pop(key) for key in self.__class__.MISC_ARGS}

        # get model params
        model_params = {
            key: kwargs.pop(key) for key in self.__class__.MODEL_ARGS
        }
        # get data params
                # Get training and pred start and end datetimes
        train_start, train_end, pred_start, pred_end = get_train_test_start_end(kwargs)
        return_y = kwargs.pop("include_prediction_y", False)
        data_config = {
            "train_start_date": train_start,
            "train_end_date": train_end,
            "pred_start_date": pred_start,
            "pred_end_date": pred_end,
            "include_prediction_y": return_y,
            "tag": misc.get("tag"),
        }
        # the rest are experiment config
        return misc, data_config, kwargs, model_params

    def save_config(self):
        """
        Save the key and values of the parser to a json file.
        """
        kwargs = vars(self.parse_args())
        with open(self.config_path, "w") as filepath:
            json.dump(kwargs, filepath)


def strtime_offset(strtime, offset_hours):
    """Give an datetime as an iso string and an offset and return a new time"""

    return (isoparse(strtime) + relativedelta(hours=offset_hours)).isoformat()


def get_train_test_start_end(kwargs):
    """
    Given kwargs return dates for training and testing.
    """
    train_end = kwargs.pop("trainend")
    train_n_hours = kwargs.pop("trainhours")
    pred_start = kwargs.pop("predstart")
    pred_n_hours = kwargs.pop("predhours")
    train_start = strtime_offset(train_end, -train_n_hours)
    pred_end = strtime_offset(pred_start, pred_n_hours)
    return train_start, train_end, pred_start, pred_end
