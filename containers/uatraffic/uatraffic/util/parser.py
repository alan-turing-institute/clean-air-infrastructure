from argparse import ArgumentParser, ArgumentTypeError
from cleanair.mixins import (
    SecretFileParserMixin,
    VerbosityMixin,
)
from .mixins import BaselineParserMixin
from datetime import datetime, timedelta


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
            default="yesterday",
            help="Timestamp for beginning of comparison day.",
            type=self.validate_type,
        )

    def validate_type(self, datestr):

        if datestr == "yesterday":
            return (datetime.today() - timedelta(days=1)).date()

        else:
            try:
                return datestr.fromisoformat()
            except ValueError:
                raise ArgumentTypeError("Not a valid iso date: {}".format(datestr))
