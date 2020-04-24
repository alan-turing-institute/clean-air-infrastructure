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


class DatabaseSetupParser(SecretFileParserMixin, ArgumentParser):
    """Argument parsing for inserting static datafiles"""

    def __init__(self, datasets, **kwargs):
        super().__init__(**kwargs)

        self.add_argument(
            "-t",
            "--sas-token",
            type=str,
            required=True,
            help="sas token to access the cleanair datastore container",
        )
        self.add_argument(
            "-u",
            "--account_url",
            type=str,
            default="https://londonaqdatasets.blob.core.windows.net",
            help="URL of storage account",
        )
        self.add_argument(
            "-c",
            "--storage-container-name",
            type=str,
            default="londonaqdatasets",
            help="Name of the storage container where the Terraform backend will be stored",
        )
        self.add_argument(
            "-d",
            "--datasets",
            nargs="+",
            type=str,
            choices=datasets,
            default=datasets,
            help="A list of datasets to include",
        )
        self.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="Increase verbosity by one step for each occurence",
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
