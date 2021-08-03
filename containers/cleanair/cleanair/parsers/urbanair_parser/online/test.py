"""CLI for production models"""

from pathlib import Path
import typer
from ....types import ExperimentName
from ..shared_args import ExperimentDir
from .utils import StaticDynamic, run_experiment_online

app = typer.Typer(help="Test CLI")

# The test_svgp functions are not implemented
# @app.command()
# def svgp(
#     static_or_dynamic: StaticDynamic, experiment_root: Path = ExperimentDir
# ) -> None:
#     """Run the test SVGP model"""
#     if static_or_dynamic == StaticDynamic.dynamic:
#         experiment_name = ExperimentName.production_svgp_dynamic
#     else:
#         experiment_name = ExperimentName.production_svgp_static
#     run_experiment_online(experiment_name, experiment_root=experiment_root)
#
#
# @app.command()
def mrdgp(
    static_or_dynamic: StaticDynamic, experiment_root: Path = ExperimentDir
) -> None:
    """Run the test MRDGP model"""
    if static_or_dynamic == StaticDynamic.dynamic:
        experiment_name = ExperimentName.test_mrdgp_dynamic
    else:
        experiment_name = ExperimentName.test_mrdgp_static
    run_experiment_online(experiment_name, experiment_root=experiment_root)
