

class BaselineParserMixin:

    def __init__(self, nhours=24, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-b",
            "--baseline_start",
            default="2020-02-10",
            help="Timestamp for beginning of baseline period."
        )
        self.add_argument(
            "-e",
            "--baseline_end",
            default="2020-03-02",
            help="Timestamp for end of baseline period."
        )
        self.add_argument(
            "-t",
            "--tag",
            default="normal",
            choices=["normal", "lockdown"],
            help="The tag for the baseline period.",
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

class ModellingParserMixin:

    def __init__(self, n_inducing_points=24, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-i",
            "--n_inducing_points",
            default=n_inducing_points,
            type=int,
            help="Number of inducing points. Default is 24."
        )
        self.add_argument(
            "-k",
            "--kernel",
            choices=["matern32", "rbf", "periodic"],
            default="matern32",
            help="The name of the kernel to run.",
        )
        self.add_argument(
            "--epochs",
            type=int,
            default=2000,
            help="Number of epochs to train model for.",
        )
        self.add_argument(
            "-m",
            "--model_name",
            default="svgp",
            help="Name of the model to run.",
        )
