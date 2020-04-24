
from argparse import ArgumentParser, ArgumentTypeError
from cleanair.mixins import (
    SecretFileParserMixin,
    VerbosityMixin,
)
from .mixins import BaselineParserMixin, ModellingParserMixin, KernelParserMixin

class TrafficModelParser(
    BaselineParserMixin,
    ModellingParserMixin,
    KernelParserMixin,
    SecretFileParserMixin,
    VerbosityMixin,
    ArgumentParser
):
    """Parser for running lockdown models."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
    
    # def parse_args(self, args=None, namespace=None):
    #     args = super().parse_args(args=args, namespace=namespace)
    #     if not args.detectors:
    #         raise ArgumentTypeError("No detector ids passed.")
    #     return args

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
