"""
The model fitting parser.
"""

from .base_parser import CleanAirParser


class ModelFitParser(CleanAirParser):
    """
    A parser for the model fitting entrypoint.
    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)

