"""
Mixins which are used by multiple argument parsers
"""
import os
import json
from argparse import ArgumentTypeError, Action
from dateutil.parser import isoparse


class LoadCopernicusKey(Action):
    "Attempt to load a copernicus key for a secret directory if not key provided"

    def __call__(self, parser, namespace, values, option_string=None):
        "Load copernicus key if missing"

        if values == "":
            try:
                with open(
                    os.path.abspath(
                        os.path.join(os.sep, "secrets", "copernicus_secrets.json")
                    )
                ) as f_secret:
                    data = json.load(f_secret)
                    values = data["copernicus_key"]
            except (json.decoder.JSONDecodeError, FileNotFoundError):
                values = None

        setattr(namespace, self.dest, values)


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


class ParseNHours(Action):
    "Parse ndays into nhours"

    def __call__(self, parser, namespace, values, option_string=None):
        "Replace nhours with ndays*24"

        setattr(namespace, "nhours", values * 24)


class SecretFileParserMixin:
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


class DurationParserMixin:
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
            action=ParseNHours,
        )

    @staticmethod
    def is_iso_string(isostring):
        """Check if isostring is a valid iso string

        Arguments:
            isostring (str): An iso string
        """
        try:
            isoparse(isostring)
        except ValueError:
            return False

        return True

    def check_upto(self, value):
        "validate the upto argument"

        acceptable_values = ["lasthour", "now", "today", "tomorrow", "yesterday"]

        if not isinstance(value, str):
            raise ArgumentTypeError("%s is not of type str" % value)

        if (value in acceptable_values) or self.is_iso_string(value):
            return value

        raise ArgumentTypeError("%s is not a valid argument" % value)


class VerbosityMixin:
    """
    Parser for any entrypoint which allows verbosity to be set
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument("-v", "--verbose", action="count", default=0)


class SourcesMixin:
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


class WebMixin:
    """Parser for any entrypoint which needs to display sqlquery results
    as an html table"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-w",
            "--web",
            default=False,
            action="store_true",
            help="Open a browser to show available data. Else print to console",
        )


class InsertMethodMixin:
    """Parser for any entrypoint which needs to set a insert method
    when inserting data into a database.
    Missing means only process and insert data that is known to be missing from the database
    All means insert all data even if it isnt missing. Can be used to overwrite existing data
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-m", "--method", default="missing", type=str, choices=["missing", "all"]
        )


class CopernicusMixin:
    """Argument parsing for Satellite readings"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-k",
            "--copernicus-key",
            type=str,
            action=LoadCopernicusKey,
            required=True,
            help="""copernicus key for accessing satellite data.
If provided with no value will try to load from 'secrets/copernicus_secrets.json'""",
        )
