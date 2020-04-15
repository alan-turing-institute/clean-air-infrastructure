from argparse import ArgumentParser, ArgumentTypeError
from cleanair.mixins import (
    SecretFileParserMixin,
    VerbosityMixin,
)
from .mixins import BaselineParserMixin


class BaselineParser(
    BaselineParserMixin, SecretFileParserMixin, VerbosityMixin, ArgumentParser,
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
