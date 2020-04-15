
from argparse import ArgumentParser, ArgumentTypeError
from cleanair.mixins import (
    SecretFileParserMixin,
    VerbosityMixin,
)
from .mixins import BaselineParserMixin, ModellingParserMixin

class TrafficModelParser(
    BaselineParserMixin,
    ModellingParserMixin,
    SecretFileParserMixin,
    VerbosityMixin,
    ArgumentParser
):
    """Parser for running lockdown models."""
    def __init__(self, nhours=24, **kwargs):
        super().__init__(**kwargs, nhours=nhours)
        self.add_argument(
            "-c",
            "--cluster_id",
            choices=["local", "pearl", "azure"],
            default="local",
        )
        self.add_argument(
            "-x",
            "--experiment",
            default="daily",
            help="Name of the experiment.",
        )
        self.add_argument(
            "--root",
            default="../experiments",
            help="Root to experiments directory."
        )
        self.add_argument(
            "-d",
            "--detectors",
            nargs="+",
            default=["N00/002e1","N00/002g1","N13/016a1"],
            help="List of SCOOT detectors to forecast for, (default: all of them).",
        )
        self.add_argument(
            "--batch_start",
            default=None,
            type=int,
            help="Index of detector to start at during batching.",
        )
        self.add_argument(
            "--batch_size",
            default=None,
            type=int,
            help="Size of the batch.",
        )
    
    def parse_args(self):
        args = super().parse_args()
        if not args.detectors:
            raise ArgumentTypeError("No detector ids passed.")
        return args

class BaselineParser(
    BaselineParserMixin,
    SecretFileParserMixin,
    VerbosityMixin,
    ArgumentParser,
):
    """
    Parser for querying a recent day against a baseline.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-l",
            "--comparison_start",
            default="2020-03-30",
            help="Timestamp for beginning of comparison day.",
        )
