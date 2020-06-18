"""
Mixins for traffic parsers.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from argparse import Namespace
    from cleanair.mixins import ScootQueryMixin

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
        "maxiter",
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
            "--maxiter",
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

class ScootModellingSubParserMixin:
    """Add custom subparsers for batch and testing scoot models."""

    def add_custom_subparsers(
        self, dest: str = "command", batch: bool = True, test: bool = True, **kwargs,
    ):
        """
        Add subparsers including test, batch.

        Args:
            batch (Optional): If true add a batch subparser.
            dest (Optional): Key for accessing which subparser was executed.
            test (Optional): If true add a test subparser.
        """
        subparsers = self.add_subparsers(dest=dest, **kwargs)
        if batch:
            batch_parser = subparsers.add_parser("batch")
            batch_parser.add_argument(
                "--batch_start",
                default=None,
                type=int,
                help="Index of detector to start at during batching.",
            )
            batch_parser.add_argument(
                "--batch_size", default=None, type=int, help="Size of the batch.",
            )
        if test:
            test_parser = subparsers.add_parser("test")
            test_parser.add_argument(
                "-d",
                "--detectors",
                nargs="+",
                default=["N00/002e1", "N00/002g1", "N13/016a1"],
                help="List of SCOOT detectors to model.",
            )
            test_parser.add_argument(
                "--dryrun",
                action="store_true",
                help="Log how the model would train without executing.",
            )

    @staticmethod
    def detectors_from_args(traffic_query: ScootQueryMixin, args: Namespace):
        """Given a scoot query object and some args, get a list of detectors.

        Args:
            traffic_query: Scoot query object.
            args: Parsed arguments of this parser.
        """
        if args.command == "test":
            return args.detectors
        # get list of scoot detectors
        if args.command == "batch":
            detector_df = traffic_query.get_scoot_detectors(
                start=args.batch_start,
                end=args.batch_start + args.batch_size,
                output_type="df",
            )
        else:
            detector_df = traffic_query.get_scoot_detectors(output_type="df")
        return list(detector_df["detector_id"].unique())
