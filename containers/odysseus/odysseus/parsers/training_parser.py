"""
Parsers for training a model.
"""

from argparse import ArgumentParser
from cleanair.mixins import (
    DurationParserMixin,
    SecretFileParserMixin,
    VerbosityMixin,
)
from .parser_mixins import (
    BaselineParserMixin,
    InstanceParserMixin,
    ModellingParserMixin,
    KernelParserMixin,
    PreprocessingParserMixin,
    ScootModellingSubParserMixin,
)
# pylint: disable=too-many-ancestors


class TrainLockdownModelParser(
    BaselineParserMixin,
    InstanceParserMixin,
    ModellingParserMixin,
    KernelParserMixin,
    PreprocessingParserMixin,
    ScootModellingSubParserMixin,
    SecretFileParserMixin,
    VerbosityMixin,
    ArgumentParser,
):
    """Parser for running lockdown models."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_argument(
            "-x", "--experiment", default="daily", help="Name of the experiment.",
        )
        self.add_argument(
            "--root", default="../experiments", help="Root to experiments directory."
        )

class TrainScootModelParser(
    DurationParserMixin,
    InstanceParserMixin,
    ModellingParserMixin,
    KernelParserMixin,
    PreprocessingParserMixin,
    ScootModellingSubParserMixin,
    ArgumentParser,
):
    """Parser for training scoot models for the air quality inputs."""
