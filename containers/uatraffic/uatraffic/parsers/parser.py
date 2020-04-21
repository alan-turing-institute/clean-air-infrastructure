"""Parsers for the uatraffic module and their entrypoints."""

from argparse import ArgumentParser, ArgumentTypeError
from datetime import datetime, timedelta
from dateutil.parser import isoparse
from cleanair.mixins import (
    SecretFileParserMixin,
    VerbosityMixin,
)


class BaselineParser(
    SecretFileParserMixin, VerbosityMixin, ArgumentParser,
):
    """
    Parser for querying a recent day against a baseline.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-l",
            "--comparison_end_date",
            default="yesterday",
            help="Timestamp for beginning of comparison day.",
            type=validate_type,
        )
        self.add_argument(
            "-n",
            "--ndays",
            default=4,
            help="Timestamp for beginning of comparison day.",
            type=int,
        )
        self.add_argument(
            "-b",
            "--backfill",
            action="store_true",
            default=True,
            help="""Backfill to earliest available date.
            Will ignore ndays and calculate from the end of the baseline period""",
        )


def validate_type(datestr):
    """
    Ensure the datestr passed in valid.
    If yesterday is passed then return yesterdays date.
    """
    if datestr == "yesterday":
        return (datetime.today() - timedelta(days=1)).date()

    try:
        return isoparse(datestr)
    except ValueError:
        raise ArgumentTypeError("Not a valid iso date: {}".format(datestr))
