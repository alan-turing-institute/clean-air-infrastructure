"""
A base class for cleanair parsers.
"""
import json
import argparse
import datetime
from ..mixins import SecretFileParserMixin, VerbosityMixin
from ..timestamps import as_datetime


class BaseModelParser(SecretFileParserMixin, VerbosityMixin, argparse.ArgumentParser):
    """
    Parser for CleanAir model entrypoints.
    """

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
            "-t",
            "--tag",
            type=str,
            default="test",
            help="Tag to identify the model fit.",
        )
        self.add_argument(
            "-d",
            "--config_dir",
            default="./",
            help="Filepath to directory to store model and data.",
        )
        # whether to read and write from the database or locally
        self.add_argument(
            "--local-read",
            action="store_true",
            default=False,
            help="Read local training/test data from config_dir.",
        )
        self.add_argument(
            "-r",
            "--results-dir",
            type=str,
            default="CONFIG_DIR",
            help="Filepath to the directory of results.",
        )
        # optional params
        self.add_argument(
            "-y",
            "--return-y",
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
        self.add_argument(
            "--include_satellite",
            action="store_true",
            help="If passed the model will use satellite data.",
        )

        self.train_end_date = None
        self.train_start_date = None
        self.pred_start_date = None
        self.pred_end_date = None
        self.include_prediction_y = None
        self.tag = None
        self.include_satellite = False

    def parse_kwargs(self):
        """
        If the -c flag is passed, then load the config.json file
        and overwrite any fields that are passed in kwargs.
        """
        args = self.parse_args()
        kwargs = vars(args)

        # Remove any arguments which are needed for the data config
        self.include_prediction_y = kwargs.pop("return_y")
        self.include_satellite = kwargs.pop("include_satellite")
        self.tag = kwargs.pop("tag")

        # Convert timestamps into start and end datetimes
        self.train_end_date = as_datetime(kwargs.pop("trainend"))
        self.train_start_date = self.train_end_date - datetime.timedelta(
            hours=kwargs.pop("trainhours")
        )
        self.pred_start_date = as_datetime(kwargs.pop("predstart"))
        self.pred_end_date = self.pred_start_date + datetime.timedelta(
            hours=kwargs.pop("predhours")
        )

        if kwargs.pop("cleanair_config"):
            # load custom config and overwrite arguments passed
            with open(self.config_path, "r") as filepath:
                config = json.load(filepath)
            for key, value in config.items():
                if key in kwargs:
                    kwargs[key] = value
        if kwargs["results_dir"] == "CONFIG_DIR":
            kwargs["results_dir"] = kwargs["config_dir"]
        return kwargs

    def generate_data_config(self):
        """
        Return a dictionary of model data configs
        """
        # Ensure that timestamp arguments have been processed
        if not self.train_start_date:
            self.parse_kwargs()

        # Generate and return the config dictionary
        return {
            "train_start_date": self.train_start_date,
            "train_end_date": self.train_end_date,
            "pred_start_date": self.pred_start_date,
            "pred_end_date": self.pred_end_date,
            "include_satellite": self.include_satellite,
            "include_prediction_y": self.include_prediction_y,
            "train_sources": ["laqn"],
            "pred_sources": ["laqn"],    # TODO remove hardcoding
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
            "tag": self.tag,
        }

    def save_config(self):
        """
        Save the key and values of the parser to a json file.
        """
        kwargs = vars(self.parse_args())
        with open(self.config_path, "w") as filepath:
            json.dump(kwargs, filepath)
