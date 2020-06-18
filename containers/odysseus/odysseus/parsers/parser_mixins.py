"""
Mixins for traffic parsers.
"""


class BaselineParserMixin:
    """Arguments for baseline periods."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.add_argument(
            "-b",
            "--baseline_period",
            default="normal",
            choices=["normal", "lockdown"],
            help="The name of the baseline period.",
        )


class InstanceParserMixin:
    """Arguments for creating/selecting an instance."""

    INSTANCE_GROUP = [
        "tag",
        "cluster_id",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        instance_group = self.add_argument_group("instance")
        instance_group.add_argument(
            "-t",
            "--tag",
            default="validation",
            type=str,
            help="A custom tag to identify model fits.",
        )
        instance_group.add_argument(
            "-c", "--cluster_id", choices=["local", "pearl", "azure"], default="local",
        )


class PreprocessingParserMixin:
    """Parser options for preprocessing and normalising data."""

    PREPROCESSING_GROUP = [
        "features",
        "median",
        "normaliseby",
        "target",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        preprocessing_group = self.add_argument_group("preprocessing")
        preprocessing_group.add_argument(
            "--features",
            nargs="+",
            default=["time_norm"],
            help="Names of the features.",
        )
        preprocessing_group.add_argument(
            "--normaliseby",
            default="clipped_hour",
            choices=["clipped_hour", "hour", "epoch"],
            help="The method for normalizing time.",
        )
        preprocessing_group.add_argument(
            "--median",
            action="store_true",
            help="Train models on the median of the daily profile.",
        )
        preprocessing_group.add_argument(
            "--target",
            nargs="+",
            default=["n_vehicles_in_interval"],
            help="The names of the target variables.",
        )


class ModellingParserMixin:
    """Parser options for modelling."""

    MODEL_GROUP = [
        "n_inducing_points",
        "inducing_point_method",
        "max_iterations",
        "model_name",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        modelling_group = self.add_argument_group("modelling")
        modelling_group.add_argument(
            "--n_inducing_points",
            default=None,
            type=int,
            help="Number of inducing points. If not set then no inducing points are used.",
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
            "-m", "--model_name", default="svgp", help="Name of the model to run.",
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
            "--lengthscales",
            type=float,
            default=1.0,
            help="Value for lengthscale (note ARD not supported).",
        )
        kernel_group.add_argument(
            "--variance", type=float, default=1.0, help="Initial value for variance.",
        )
