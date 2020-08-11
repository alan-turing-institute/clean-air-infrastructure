"""
A base class for cleanair parsers.
"""
import argparse
from datetime import timedelta
from ..mixins import SecretFileParserMixin, VerbosityMixin
from ..timestamps import as_datetime


class ModelFittingParser(
    SecretFileParserMixin, VerbosityMixin, argparse.ArgumentParser
):
    """
    Parser for CleanAir model entrypoints.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_argument(
            "-t",
            "--tag",
            type=str,
            default="test",
            help="Tag to identify the model fit.",
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
            "--predict_training",
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
        self.add_argument(
            "--hexgrid", action="store_true", help="Predict at the hexgrid.",
        )
        self.add_argument(
            "--maxiter", default=2000, type=int, help="Number of training iterations.",
        )
        self.add_argument(
            "--git_hash", default=None, type=str, help="Hex string of git repo."
        )

    @staticmethod
    def generate_data_config(args):
        """
        Return a dictionary of model data configs
        """

        # Generate and return the config dictionary
        data_config = {
            "train_start_date": as_datetime(args.trainend)
            - timedelta(hours=args.trainhours),
            "train_end_date": as_datetime(args.trainend),
            "pred_start_date": as_datetime(args.predstart),
            "pred_end_date": as_datetime(args.predstart)
            + timedelta(hours=args.predhours),
            "include_satellite": args.include_satellite,
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
            "tag": args.tag,
        }
        if args.hexgrid:
            data_config["pred_sources"].append("hexgrid")
        return data_config
