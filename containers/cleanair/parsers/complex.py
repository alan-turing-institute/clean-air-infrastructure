"""
Complex per-entrypoint argument parsers
"""
# pylint: disable=too-many-ancestors
from argparse import ArgumentParser, ArgumentTypeError
import json
import os
from .model import BaseModelParser
from ..experiment import ValidationInstance, ProductionInstance
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
        self.add_argument(
            "-a",
            "--archive",
            dest="use_archive_data",
            action="store_true",
            help="""Use archive data rather than forecast data""",
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
    A parser for validation.
    """

    EXPERIMENT_ARGS = BaseModelParser.EXPERIMENT_ARGS + ["predict_read_local", "local_write", "no_db_write", "predict_write", "model_dir", "results_dir", "restore", "save_model_state"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_defaults(
            model_name=ValidationInstance.DEFAULT_MODEL_NAME,
            tag="validation",
            include_prediction_y=True,  # compare pred vs actual
        )
        self.add_argument(
            "-predict_read_local",
            action="store_true",
            help="Read predictions from a local file.",
        )
        # model arguments
        self.add_argument(
            "-restore",
            action="store_true",
            help="Restore the model from model_dir.",
        )
        self.add_argument(
            "-save_model_state",
            action="store_true",
            help="Save the model.",
        )
        self.add_argument(
            "-local_write",
            action="store_true",
            help="Write training/test data to config_dir.",
        )
        self.add_argument(
            "-no_db_write",
            action="store_true",
            help="Do not write result to database.",
        )
        self.add_argument(
            "-predict_write",
            action="store_true",
            help="Write a prediction to the results_dir.",
        )
        self.add_argument(
            "-model_dir",
            type=str,
            default="CONFIG_DIR",
            help="Filepath to the directory where the model is (re-)stored.",
        )
        self.add_argument(
            "-r",
            "--results_dir",
            type=str,
            default="CONFIG_DIR",
            help="Filepath to the directory of results.",
        )

    def parse_all(self):
        kwargs, data_args, xp_config, model_args = super().parse_all()
        if xp_config["results_dir"] == "CONFIG_DIR":
            xp_config["results_dir"] = xp_config["config_dir"]
        if xp_config["model_dir"] == "CONFIG_DIR":
            xp_config["model_dir"] = xp_config["config_dir"]
        model_args["model_state_fp"] = xp_config["model_dir"]
        return kwargs, data_args, xp_config, model_args


class ProductionParser(BaseModelParser):
    """
    A parser for the model fitting entrypoint.
    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.set_defaults(
            tag="production",
            model_name=ProductionInstance.DEFAULT_MODEL_NAME,
        )

class DashboardParser(ModelValidationParser):
    """
    A parser for the dashboard.
    """

    MISC_ARGS = ModelValidationParser.MISC_ARGS + ["instance_id"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-i",
            "--instance_id",
            type=str,
            help="Id of the instance to load.",
        )
