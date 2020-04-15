"""
Mixins for the uatraffic module.
"""


class BaselineParserMixin:
    """A parser for comparing against a baseline."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-t",
            "--tag",
            default="normal",
            choices=["normal", "lockdown"],
            help="The tag for the baseline period.",
        )
