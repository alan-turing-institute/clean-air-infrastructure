"""Parser for the dashboard."""

import argparse
from ..mixins import SecretFileParserMixin, VerbosityMixin


class DashboardParser(SecretFileParserMixin, VerbosityMixin, argparse.ArgumentParser):
    """Parser for the dashboard."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "--instance_id",
            type=str,
            help="Id of the instance to show the dashboard for.",
        )
