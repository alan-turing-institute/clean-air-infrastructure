
from .validation_parser import ValidationParser

class DashboardParser(ValidationParser):
    """
    A parser for the dashboard.
    """

    MISC_ARGS = ValidationParser.MISC_ARGS + ["instance_id"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-i",
            "--instance_id",
            type=str,
            help="Id of the instance to load.",
        )