"""
Mixins for traffic parsers.
"""

class BaselineParserMixin:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-t",
            "--tag",
            default="normal",
            choices=["normal", "lockdown"],
            help="The tag for the baseline period.",
        )

class ModellingParserMixin:

    def __init__(self, n_inducing_points=24, **kwargs):
        super().__init__(**kwargs)
        self.modelling_group = self.add_argument_group("modelling")
        self.modelling_group.add_argument(
            "-i",
            "--n_inducing_points",
            default=n_inducing_points,
            type=int,
            help="Number of inducing points. Default is 24."
        )
        self.modelling_group.add_argument(
            "--epochs",
            type=int,
            default=2000,
            help="Number of epochs to train model for.",
        )
        self.modelling_group.add_argument(
            "-m",
            "--model_name",
            default="svgp",
            help="Name of the model to run.",
        )
        self.modelling_group.add_argument(
            "-n",
            "--normaliseby",
            default="hour",
            choices=["hour", "epoch"],
            help="The method for normalizing time.",
        )

class KernelParserMixin:
    """Parser mixin for choosing the kernel and params."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kernel_group = self.add_argument_group("kernels") 
        self.kernel_group.add_argument(
            "-k",
            "--kernel",
            choices=["matern32", "rbf", "periodic"],
            default="matern32",
            help="The name of the kernel to run.",
        )
        self.kernel_group.add_argument(
            "--lengthscale",
            type=float,
            default=1.0,
            help="Value for lengthscale (note ARD not supported).",
        )
        self.kernel_group.add_argument(
            "--variance",
            type=float,
            default=1.0,
            help="Initial value for variance.",
        )

class PeriodicKernelParserMixin(KernelParserMixin):
    """Specific parser supporting the periodic kernel."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kernel_group.add_argument(
            "--period",
            type=float,
            default=1.0,
            help="Period of a periodic kernel.",
        )
