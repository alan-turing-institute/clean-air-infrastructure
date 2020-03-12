"""
The model fitting parser.
"""

from .base_parser import CleanAirParser
from ..experiment import ProductionInstance

class ProductionParser(CleanAirParser):
    """
    A parser for the model fitting entrypoint.
    """

    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        self.set_defaults(
            tag="production",
            model_name=ProductionInstance.DEFAULT_MODEL_NAME,
        )
