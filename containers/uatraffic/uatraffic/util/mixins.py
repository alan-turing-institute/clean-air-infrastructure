class BaselineParserMixin:
    def __init__(self, nhours=24, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-t",
            "--tag",
            default="normal",
            choices=["normal", "lockdown"],
            help="The tag for the baseline period.",
        )
