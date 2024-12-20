"""CLI for production models"""

from enum import Enum
from pathlib import Path
import typer
from ..experiment.main import metrics, run, setup, update, upload
from ....types import ExperimentName, ClusterId
from ..shared_args import ExperimentDir

app = typer.Typer(help="Production CLI")


# pylint: disable=C0103
class StaticDynamic(str, Enum):
    """Is the model static or dynamic?"""

    dynamic = "dynamic"
    static = "static"


@app.command()
def svgp(
    static_or_dynamic: StaticDynamic, experiment_root: Path = ExperimentDir
) -> None:
    """Run the production SVGP model"""
    if static_or_dynamic == StaticDynamic.dynamic:
        experiment_name = ExperimentName.production_svgp_dynamic
    else:
        experiment_name = ExperimentName.production_svgp_static
    setup(experiment_name, experiment_root=experiment_root)
    run(experiment_name, experiment_root=experiment_root)
    update(experiment_name, experiment_root=experiment_root)
    metrics(experiment_name, experiment_root=experiment_root)
    upload(experiment_name, experiment_root=experiment_root)


@app.command()
def mrdgp(
    static_or_dynamic: StaticDynamic,
    machine: ClusterId = ClusterId.nc6,
    experiment_root: Path = ExperimentDir,
) -> None:
    """Run the production MRDGP model"""
    if static_or_dynamic == StaticDynamic.dynamic:
        experiment_name = ExperimentName.production_mrdgp_dynamic
    else:
        experiment_name = ExperimentName.production_mrdgp_static
    setup(experiment_name, cluster_id=machine, experiment_root=experiment_root)
    run(experiment_name, experiment_root=experiment_root)
    update(experiment_name, experiment_root=experiment_root)
    metrics(experiment_name, experiment_root=experiment_root)
    upload(experiment_name, experiment_root=experiment_root)
