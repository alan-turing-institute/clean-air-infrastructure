"""CLI for production models"""

from enum import Enum
import typer
from ..experiment.main import run, setup, update
from ....types import ExperimentName

app = typer.Typer(help="Production CLI")


class StaticDynamic(str, Enum):
    """Is the model static or dynamic?"""

    dynamic = "dynamic"
    static = "static"


@app.command()
def svgp(static_or_dynamic: StaticDynamic) -> None:
    """Run the production SVGP model"""
    if static_or_dynamic == StaticDynamic.dynamic:
        experiment_name = ExperimentName.production_svgp_dynamic
    else:
        experiment_name = ExperimentName.production_svgp_static
    setup(experiment_name)
    run(experiment_name)
    update(experiment_name)


@app.command()
def mrdgp(static_or_dynamic: StaticDynamic) -> None:
    """Run the production MRDGP model"""
    if static_or_dynamic == StaticDynamic.dynamic:
        experiment_name = ExperimentName.production_mrdgp_dynamic
    else:
        experiment_name = ExperimentName.production_mrdgp_static
    setup(experiment_name)
    run(experiment_name)
    update(experiment_name)
