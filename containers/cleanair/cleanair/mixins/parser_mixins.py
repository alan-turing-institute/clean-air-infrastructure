"""
Mixins which are used by multiple argument parsers
"""
from argparse import ArgumentTypeError, Action



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
            type=str,
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

    def parse_args(self, args=None, namespace=None):
        """Raise an exception if the provided arguments are invalid"""
        args = super().parse_args(args, namespace)
        if args.ndays:
            args.nhours = args.ndays * 24
        if args.nhours < 1:
            raise ArgumentTypeError("Argument --nhours must be greater than 0")
        return args


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
