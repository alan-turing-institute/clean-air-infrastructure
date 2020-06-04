"""
Complex per-entrypoint argument parsers
"""
# pylint: disable=too-many-ancestors
from argparse import ArgumentParser, ArgumentTypeError, Action
import json
import os
from dateutil.parser import isoparse
from .model import BaseModelParser
from ..mixins import (
    SecretFileParserMixin,
    DurationParserMixin,
    VerbosityMixin,
    SourcesMixin,
)

class ParseSecretDict(Action):
    "Parse items into a dictionary"

    def __call__(self, parser, namespace, values, option_string=None):
        output_dict = {}
        valid_items = ["username", "password", "host", "port", "db_name", "ssl_mode"]

        if values:
            for item in values:
                split_items = item.split("=", 1)
                key = split_items[
                    0
                ].strip()  # we remove blanks around keys, as is logical
                if key not in valid_items:
                    parser.error("{} is not a valid secretfile override".format(key))
                if key == "port":
                    value = int(split_items[1])
                else:
                    value = split_items[1]

                output_dict[key] = value

        setattr(namespace, self.dest, output_dict)


class SecretFileParser(ArgumentParser):
    """
    Parser for any entrypoint which needs a secrets file
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-s",
            "--secretfile",
            default="db_secrets.json",
            help="File with connection secrets.",
        )
        self.add_argument(
            "--secret-dict",
            metavar="KEY=VALUE",
            nargs="+",
            help="Set a number of overrides for secretfile using item=value"
            "(do not put spaces before or after the = sign). "
            "Valid items are 'username', 'password', 'host', 'port', 'db_name', 'ssl_mode'",
            action=ParseSecretDict,
        )

class VerbosityParser(ArgumentParser):
    """
    Parser for any entrypoint which allows verbosity to be set
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument("-v", "--verbose", action="count", default=0)


class SourcesParser(ArgumentParser):
    """
    Parser for any entrypoint which allows verbosity to be set
    """

    def __init__(self, sources, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "--sources",
            nargs="+",
            default=sources,
            help="List of sources to process, (default: {}).".format(",".join(sources)),
        )

class DurationParser(ArgumentParser):

    """
    Parser for any entrypoint which needs a duration
    """

    def __init__(self, nhours=48, ndays=2, end="lasthour", **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-u",
            "--upto",
            type=self.check_upto,
            default=end,
            help="Time point to get data up to in iso format."
            "Or one of: 'lasthour', 'now', 'today', 'tomorrow', 'yesterday'. (default: {})."
            "To get data that includes today you would use 'tomorrow'"
            "to specify all data up to but not including tomorrows date".format(end),
        )
        time_group = self.add_mutually_exclusive_group()
        time_group.add_argument(
            "-n",
            "--nhours",
            type=int,
            default=nhours,
            help="The number of hours to request data for (default: {}).".format(
                nhours
            ),
        )
        time_group.add_argument(
            "--ndays",
            type=int,
            help="The number of days to request data for (default: {}).".format(ndays),
        )
    
    @staticmethod
    def is_iso_string(isostring):

        try:
            isoparse(isostring)
        except ValueError as error:
            return False
        
        return True

    def check_upto(self, value):

        acceptable_values = ['lasthour', 'now', 'today', 'tomorrow', 'yesterday']
        
        if not isinstance(value, str): 
            raise ArgumentTypeError("%s is not of type str" % value)

        if (value in acceptable_values) or self.is_iso_string(value):
            return value

        else:
            raise ArgumentTypeError("%s is not a valid argument" % value)


        # is_iso_string = False
        # try:
        #     isoparse(value)
        #     is_iso_string = True
        # except ValueError as error:
        #     pass
        
        # print(is_iso_string)

        # if (value not in acceptable_values) or is_iso_string:
            # raise ArgumentTypeError("%s is not valid" % value)
   

    def parse_args(self, args=None, namespace=None):
        """Raise an exception if the provided arguments are invalid"""
        args = super().parse_args(args, namespace)
        if args.ndays:
            args.nhours = args.ndays * 24
        if args.nhours < 1:
            raise ArgumentTypeError("Argument --nhours must be greater than 0")
        return args

class StaticFeatureArgumentParser(
    SecretFileParserMixin, VerbosityMixin, ArgumentParser,
):
    """Static feature Parser"""


class SourceParser(SourcesMixin, ArgumentParser):
    """Sources Parser"""


class FeatureSourceParser(ArgumentParser):
    """Sources Parser"""

    def __init__(self, feature_sources, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "--feature-source",
            type=str,
            required=True,
            choices=feature_sources,
            help="List of sources to process, (default: {}).".format(
                ",".join(feature_sources)
            ),
        )


class FeatureNameParser(ArgumentParser):
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
            except (json.decoder.JSONDecodeError, FileNotFoundError):
                args.copernicus_key = None
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
