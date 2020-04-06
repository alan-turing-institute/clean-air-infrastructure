"""
Complex per-entrypoint argument parsers
"""
# pylint: disable=too-many-ancestors
from argparse import ArgumentParser, ArgumentTypeError
import json
import os
from .model import BaseModelParser
from ..mixins import (
    SecretFileParserMixin,
    DurationParserMixin,
    VerbosityMixin,
    SourcesMixin,
)


class SatelliteArgumentParser(
    DurationParserMixin, SecretFileParserMixin, VerbosityMixin, ArgumentParser
):
    """Argument parsing for Satellite readings"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-k",
            "--copernicus-key",
            type=str,
            default="",
            help="copernicus key for accessing satellite data.",
        )

    def parse_args(self, args=None, namespace=None):
        """
        Check whether we have the Copernicus key and try to retrieve it from a local
        secrets file if not
        """
        args = super().parse_args(args, namespace)
        if not args.copernicus_key:
            try:
                with open(
                    os.path.abspath(
                        os.path.join(os.sep, "secrets", "copernicus_secrets.json")
                    )
                ) as f_secret:
                    data = json.load(f_secret)
                    args.copernicus_key = data["copernicus_key"]
            except json.decoder.JSONDecodeError:
                raise ArgumentTypeError("Could not determine copernicus_key")
        return args


class ScootReadingArgumentParser(
    DurationParserMixin, SecretFileParserMixin, VerbosityMixin, ArgumentParser
):
    """Argument parsing for SCOOT readings"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-i",
            "--aws-key-id",
            type=str,
            default="",
            help="AWS key ID for accessing TfL SCOOT data.",
        )
        self.add_argument(
            "-k",
            "--aws-key",
            type=str,
            default="",
            help="AWS key for accessing TfL SCOOT data.",
        )

    def parse_args(self, args=None, namespace=None):
        """
        Check whether we have AWS connection information and try to retrieve it from a
        local secrets file if not
        """
        args = super().parse_args(args, namespace)
        if not (args.aws_key_id and args.aws_key):
            try:
                with open(
                    os.path.abspath(os.path.join(os.sep, "secrets", "aws_secrets.json"))
                ) as f_secret:
                    data = json.load(f_secret)
                    args.aws_key_id = data["aws_key_id"]
                    args.aws_key = data["aws_key"]
            except json.decoder.JSONDecodeError:
                raise ArgumentTypeError(
                    "Could not determine SCOOT aws_key_id or aws_key"
                )
        return args


class ScootForecastFeatureArgumentParser(
    DurationParserMixin,
    SecretFileParserMixin,
    SourcesMixin,
    VerbosityMixin,
    ArgumentParser,
):
    """Argument parsing for converting SCOOT forecasts into model features"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-f",
            "--forecasthrs",
            type=int,
            default=72,
            help="The number of hours into the future to predict for (default: 72).",
        )
        self.add_argument(
            "-d",
            "--detectors",
            nargs="+",
            default=[],
            help="List of SCOOT detectors to forecast for, (default: all of them).",
        )

class ScootParser(
    SecretFileParserMixin,
    VerbosityMixin,
    ArgumentParser
):
    """Parser for running lockdown models."""
    def __init__(self, nhours=24, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-x",
            "--experiment",
            default="daily",
            help="Name of the experiment.",
        )
        self.add_argument(
            "--nhours",
            type=int,
            default=nhours,
            help="The number of hours to request data for (default: {}).".format(
                nhours
            ),
        )
        self.add_argument(
            "--root",
            default="../../../experiments",
            help="Root to experiments directory."
        )
        self.add_argument(
            "-r",
            "--rolls",
            type=int,
            default=1,
            help="Number of times to roll forward timeframe."
        )
        self.add_argument(
            "-l",
            "--lockdown_start",
            default="2020-03-23T00:00:00",
            help="The start datetime of lockdown period."
        )
        self.add_argument(
            "-n",
            "--normal_start",
            default="2020-02-10T00:00:00",
            help="The start datetime of normal period."
        )
        self.add_argument(
            "-u",
            "--user_settings_filepath",
            default="../../terraform/.secrets/user_settings.json",
            help="Filepath to user settings."
        )
        self.add_argument(
            "-d",
            "--detectors",
            nargs="+",
            default=["N00/002e1","N00/002g1","N13/016a1"],
            help="List of SCOOT detectors to forecast for, (default: all of them).",
        )
    
    def parse_args(self):
        args = super().parse_args()
        if not args.detectors:
            raise ArgumentTypeError("No detector ids passed.")
        return args

class ModelValidationParser(BaseModelParser):
    """
    A parser for model validation.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "--predict-read-local",
            action="store_true",
            help="Read predictions from a local file.",
        )


class ModelFitParser(BaseModelParser):
    """
    A parser for the model fitting entrypoint.
    """

    def __init__(self, **kwargs):
        """
        Should be able to:
            - read training/test data from DB (default)
            - read training/test data from directory
            - write training/test data to directory
            - write result to DB (default)
            - turn off writing to DB (overwrite default)
            - write results to file
        """
        super().__init__(**kwargs)
        self.add_argument(
            "--local-write",
            action="store_true",
            help="Write training/test data to config_dir.",
        )
        self.add_argument(
            "--no-db-write",
            action="store_true",
            help="Do not write result to database.",
        )
        self.add_argument(
            "--predict-write",
            action="store_true",
            help="Write a prediction to the results_dir.",
        )
        self.add_argument(
            "--model-dir",
            type=str,
            default="CONFIG_DIR",
            help="Filepath to the directory where the model is (re-)stored.",
        )

    def parse_kwargs(self):
        kwargs = super().parse_kwargs()
        if kwargs["model_dir"] == "CONFIG_DIR":
            kwargs["model_dir"] = kwargs["model_dir"]
        return kwargs
