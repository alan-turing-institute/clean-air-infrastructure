"""CLI for production models"""

from pathlib import Path
import typer
from ....types import ExperimentName
from ..shared_args import ExperimentDir
from .utils import StaticDynamic, run_experiment_online

app = typer.Typer(help="Production CLI")


@app.command()
def svgp(
    static_or_dynamic: StaticDynamic, experiment_root: Path = ExperimentDir
) -> None:
    """Run the production SVGP model"""
    if static_or_dynamic == StaticDynamic.dynamic:
        experiment_name = ExperimentName.production_svgp_dynamic
    else:
        experiment_name = ExperimentName.production_svgp_static
    run_experiment_online(experiment_name, experiment_root=experiment_root)


@app.command()
def mrdgp(
    static_or_dynamic: StaticDynamic, experiment_root: Path = ExperimentDir
) -> None:
    """Run the production MRDGP model"""
    if static_or_dynamic == StaticDynamic.dynamic:
        experiment_name = ExperimentName.production_mrdgp_dynamic
    else:
        experiment_name = ExperimentName.production_mrdgp_static
    run_experiment_online(experiment_name, experiment_root=experiment_root)
