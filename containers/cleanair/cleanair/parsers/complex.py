"""
Complex per-entrypoint argument parsers
"""
# pylint: disable=too-many-ancestors
from argparse import ArgumentParser, ArgumentTypeError
import json
import os
from ..mixins import (
    SecretFileParserMixin,
    DurationParserMixin,
    VerbosityMixin,
    SourcesMixin,
    CopernicusMixin,
)


class FeatureSourceParser(ArgumentParser):
    """Sources Parser"""

    def __init__(self, feature_sources, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "--feature-source",
            type=str,
            required=True,
            choices=feature_sources,
            help="Source of features to process. Can only process one at a time",
        )


class FeatureNameParser(ArgumentParser):
    """Parser arguments for choosing which features to process"""

    def __init__(self, feature_names, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "--feature-name",
            required=False,
            nargs="+",
            choices=feature_names,
            help="Specify feature names to run. If not provided will process all feature names",
            type=str,
        )


class DataBaseRoleParser(SecretFileParserMixin, VerbosityMixin, ArgumentParser):
    """Argument parser for configuring database roles"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-c",
            "--config-file",
            type=str,
            required=True,
            help="Location of configuration file",
        )


class DatabaseSetupParser(SecretFileParserMixin, VerbosityMixin, ArgumentParser):
    """Argument parsing for inserting static datafiles"""


class SatelliteArgumentParser(CopernicusMixin, ArgumentParser):
    """Argument parsing for Satellite readings"""


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
                    os.path.abspath(
                        os.path.join(os.sep, "secrets", "aws_secrets.json")
                    ),
                    encoding="utf-8",
                ) as f_secret:
                    data = json.load(f_secret)
                    args.aws_key_id = data["aws_key_id"]
                    args.aws_key = data["aws_key"]
            except json.decoder.JSONDecodeError as decode_error:
                raise ArgumentTypeError(
                    "Could not determine SCOOT aws_key_id or aws_key"
                ) from decode_error
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
