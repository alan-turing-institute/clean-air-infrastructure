

class BaselineParserMixin:

    def __init__(self, nhours=24):
        self.add_argument(
            "-b",
            "--baseline_start",
            default="2020-02-10",
            help="Timestamp for beginning of baseline period."
        )
        self.add_argument(
            "-e",
            "--baseline-end",
            default="2020-03-02",
            help="Timestamp for end of baseline period."
        )
        self.add_argument(
            "-t",
            "--tag",
            default="normal",
            options=["normal", "lockdown"],
            help="The tag for the baseline period.",
        )
        self.add_argument(
            "--nhours",
            type=int,
            default=nhours,
            help="The number of hours to request data for (default: {}).".format(
                nhours
            ),
        )