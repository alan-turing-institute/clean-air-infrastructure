"""
Mixins for traffic parsers.
"""

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
        self.add_argument(
            "-n",
            "--normalizeby",
            default="hour",
            choices=["hour"],
            help="The method for normalizing time.",
        )

class KernelParserMixin:
    """Parser mixin for choosing the kernel and params."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)      
        self.add_argument(
            "-k",
            "--kernel",
            choices=["matern32", "rbf", "periodic"],
            default="matern32",
            help="The name of the kernel to run.",
        )
        self.add_argument(
            "--lengthscales",
            type=float,
            default=1.0,
            help="Value for lengthscale (note ARD not supported).",
        )
        self.add_argument(
            "--variance",
            type=float,
            default=1.0,
            help="Initial value for variance.",
        )

class PeriodicKernelParserMixin(KernelParserMixin):
    """Specific parser supporting the periodic kernel."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "--period",
            type=float,
            default=1.0,
            help="Period of a periodic kernel.",
        )
