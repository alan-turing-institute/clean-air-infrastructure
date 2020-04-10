
from argparse import ArgumentParser, ArgumentTypeError
from cleanair.mixins import (
    SecretFileParserMixin,
    VerbosityMixin,
)
from .mixins import BaselineParserMixin

class ScootParser(
    BaselineParserMixin,
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
            "--root",
            default="../../../experiments",
            help="Root to experiments directory."
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

class BaselineParser(
    BaselineParserMixin,
    ArgumentParser,
    SecretFileParserMixin,
    VerbosityMixin
):
    """
    Parser for querying a recent day against a baseline.
    """
    def __init__(self, nhours=24):
        super().__init__(nhours=nhours)
        self.add_argument(
            "-l",
            "--latest_start",
            default="2020-04-06",
            help="Timestamp for beginning of latest day.",
        )
