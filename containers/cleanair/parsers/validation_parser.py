"""
Parsers for validation that must read model fit data.
"""

from .base_parser import CleanAirParser


class ValidationParser(CleanAirParser):
    """
    A parser for validation.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-predict_read_local",
            action="store_true",
            help="Read predictions from a local file.",
        )
