"""Setup, run and update experiments"""

from typing import Callable
from pathlib import Path
import typer
from ....experiment import SetupAirQualityExperiment, generate_air_quality_experiment
from ..shared_args import ExperimentDir
from ..state import state
from ....types import ExperimentName

app = typer.Typer(help="Experiment CLI")


@app.command
def setup(experiment_name: ExperimentName, experiment_dir: Path = ExperimentDir):
    """Compare the effect of changing static features"""
    secretfile: str = state["secretfile"]
    experiment_name = "static_features"
    experiment_dir = experiment_dir / experiment_name

    # get the function that will generate instances
    experiment_generator_function: Callable = getattr(
        generate_air_quality_experiment, experiment_name
    )

    # generate the instances
    instances = experiment_generator_function()

    # create an experiment from generated instances
    setup_experiment = SetupAirQualityExperiment(experiment_dir, secretfile=secretfile)
    map(setup_experiment.add_instance, instances)

    # load datasets
    setup_experiment.load_datasets()
    map(setup_experiment.write_instance_to_file, setup_experiment.get_instance_ids())
