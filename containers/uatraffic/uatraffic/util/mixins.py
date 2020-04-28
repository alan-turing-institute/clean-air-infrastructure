"""
Mixins for traffic parsers.
"""

class BaselineParserMixin:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_argument(
            "-t",
            "--tag",
            default="validation",
            type=str,
            help="A custom tag to identify model fits.",
        )
        self.add_argument(
            "-b",
            "--baseline_period",
            default="normal",
            choices=["normal", "lockdown"],
            help="The name of the baseline period.",
        )

class ModellingParserMixin:
    """Parser options for modelling."""

    MODEL_GROUP = [
        "n_inducing_points",
        "inducing_point_method",
        "max_iterations",
        "model_name",
        "normaliseby",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        modelling_group = self.add_argument_group("modelling")
        modelling_group.add_argument(
            "--n_inducing_points",
            default=None,
            type=int,
            help="Number of inducing points. Default is 24."
        )
        modelling_group.add_argument(
            "--inducing_point_method",
            default="random",
            type=str,
            help="Method for optimizing inducing points.",
        )
        modelling_group.add_argument(
            "--max_iterations",
            type=int,
            default=2000,
            help="Max number of iterations to train model.",
        )
        modelling_group.add_argument(
            "-m",
            "--model_name",
            default="svgp",
            help="Name of the model to run.",
        )
        modelling_group.add_argument(
            "--normaliseby",
            default="clipped_hour",
            choices=["clipped_hour", "hour", "epoch"],
            help="The method for normalizing time.",
        )

class KernelParserMixin:
    """Parser mixin for choosing the kernel and params."""

    KERNEL_GROUP = ["kernel", "lengthscale", "variance"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        kernel_group = self.add_argument_group("kernels") 
        kernel_group.add_argument(
            "-k",
            "--kernel",
            choices=["matern32", "rbf", "periodic"],
            default="rbf",
            help="The name of the kernel to run.",
        )
        kernel_group.add_argument(
            "--lengthscale",
            type=float,
            default=1.0,
            help="Value for lengthscale (note ARD not supported).",
        )
        kernel_group.add_argument(
            "--variance",
            type=float,
            default=1.0,
            help="Initial value for variance.",
        )

class PeriodicKernelParserMixin(KernelParserMixin):
    """Specific parser supporting the periodic kernel."""

    KERNEL_GROUP = KernelParserMixin.KERNEL_GROUP + ["period"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kernel_group.add_argument(
            "--period",
            type=float,
            default=1.0,
            help="Period of a periodic kernel.",
        )
