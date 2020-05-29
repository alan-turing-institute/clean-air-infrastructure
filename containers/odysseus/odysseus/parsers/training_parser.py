"""
Parsers for training a model.
"""

from argparse import ArgumentParser
from cleanair.mixins import (
    SecretFileParserMixin,
    VerbosityMixin,
)
from .parser_mixins import (
    BaselineParserMixin,
    InstanceParserMixin,
    ModellingParserMixin,
    KernelParserMixin,
    PreprocessingParserMixin,
)

class TrainTrafficModelParser(  # pylint: disable=too-many-ancestors
    BaselineParserMixin,
    InstanceParserMixin,
    ModellingParserMixin,
    KernelParserMixin,
    PreprocessingParserMixin,
    SecretFileParserMixin,
    VerbosityMixin,
    ArgumentParser
):
    """Parser for running lockdown models."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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

    def add_custom_subparsers(
        self,
        dest: str = "command",
        batch: bool = True,
        test: bool = True,
        **kwargs,
    ):
        """
        Add subparsers including test, batch.

        Args:
            batch (Optional): If true add a batch subparser.
            dest (Optional): Key for accessing which subparser was executed.
            test (Optional): If true add a test subparser.
        """
        subparsers = self.add_subparsers(dest=dest, **kwargs)
        if batch:
            batch_parser = subparsers.add_parser("batch")
            batch_parser.add_argument(
                "--batch_start",
                default=None,
                type=int,
                help="Index of detector to start at during batching.",
            )
            batch_parser.add_argument(
                "--batch_size",
                default=None,
                type=int,
                help="Size of the batch.",
            )
        if test:
            test_parser = subparsers.add_parser("test")
            test_parser.add_argument(
                "-d",
                "--detectors",
                nargs="+",
                default=["N00/002e1", "N00/002g1", "N13/016a1"],
                help="List of SCOOT detectors to model.",
            )
            test_parser.add_argument(
                "--dryrun",
                action="store_true",
                help="Log how the model would train without executing."
            )
