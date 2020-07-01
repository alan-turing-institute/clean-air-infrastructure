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
