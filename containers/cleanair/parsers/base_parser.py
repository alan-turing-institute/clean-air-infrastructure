"""
A base class for cleanair parsers.
"""

import json
import argparse
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta


class CleanAirParser(argparse.ArgumentParser):
    """
    The base cleanair entrypoint parser.
    """

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
            default="svgp",
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
            default="../../terraform/.secrets/db_secrets.json",
            help="File with connection secrets.",
        )
        self.add_argument(
            "-d",
            "--config_dir",
            default="./",
            help="Filepath to directory to store model and data.",
        )
        self.add_argument("-v", "--verbose", action="count", default=0)
        # whether to read and write from the database or locally
        self.add_argument(
            "-local_read",
            action="store_true",
            help="Read local training/test data from config_dir.",
        )
        self.add_argument(
            "-r",
            "--results_dir",
            type=str,
            default="CONFIG_DIR",
            help="Filepath to the directory of results.",
        )
        # optional params
        self.add_argument(
            "-y",
            "--return_y",
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
            default="2020-01-30T00:00:00",
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
            default="2020-01-30T00:00:00",
            help="The first datetime (YYYY-MM-DD HH:MM:SS) to get model data for prediction.",
        )
        self.add_argument(
            "--predhours",
            type=int,
            default=48,
            help="The number of hours to predict for",
        )

    def parse_kwargs(self):
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
                # else:
                # raise KeyError("{k} not a valid argument.".format(k=key))
        if kwargs["results_dir"] == "CONFIG_DIR":
            kwargs["results_dir"] = kwargs["config_dir"]
        return kwargs

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


def get_data_config_from_kwargs(kwargs):
    """
    Return a dictionary of model data configs given parser arguments.
    """
    # Get training and pred start and end datetimes
    train_start, train_end, pred_start, pred_end = get_train_test_start_end(kwargs)
    return_y = kwargs.pop("return_y")
    tag = kwargs.pop("tag")

    # Model configuration
    model_config = {
        "train_start_date": train_start,
        "train_end_date": train_end,
        "pred_start_date": pred_start,
        "pred_end_date": pred_end,
        "include_satellite": True,
        "include_prediction_y": return_y,
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
        "tag": tag,
    }
    return model_config


def pop_non_model_data_keys(kwargs):
    """
    Pop keys/values that model_data does not accept.
    """
    return {
        key: kwargs.pop(key)
        for key in set(kwargs.keys()) - {"secretfile", "config_dir"}
    }
