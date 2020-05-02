"""
Mixins which are used by multiple argument parsers
"""
from argparse import ArgumentTypeError


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


class DurationParserMixin:
    """
    Parser for any entrypoint which needs a duration
    """

    def __init__(self, nhours=48, end="lasthour", **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-e",
            "--end",
            type=str,
            default=end,
            help="The last time point to get data for in iso format (default: {}).".format(
                end
            ),
        )
        self.add_argument(
            "-n",
            "--nhours",
            type=int,
            default=nhours,
            help="The number of hours to request data for (default: {}).".format(
                nhours
            ),
        )

    def parse_args(self, args=None, namespace=None):
        """Raise an exception if the provided arguments are invalid"""
        args = super().parse_args(args, namespace)
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
