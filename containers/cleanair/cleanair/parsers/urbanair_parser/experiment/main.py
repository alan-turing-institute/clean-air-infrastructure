"""Setup, run and update experiments"""

from typing import Callable, List
from pathlib import Path
import typer
from ....experiment import RunnableAirQualityExperiment, SetupAirQualityExperiment, generate_air_quality_experiment
from ....mixins import InstanceMixin
from ..shared_args import ExperimentDir
from ..state import state
from ....types import ExperimentName

app = typer.Typer(help="Experiment CLI")


@app.command()
def setup(experiment_name: ExperimentName, experiment_dir: Path = ExperimentDir) -> None:
    """Setup an experiment: load data + setup model parameters"""
    secretfile: str = state["secretfile"]
    experiment_dir = experiment_dir / experiment_name.value

    # get the function that will generate instances
    experiment_generator_function: Callable[str, List[InstanceMixin]] = getattr(
        generate_air_quality_experiment, experiment_name.value
    )
    # generate the instances
    instance_list = experiment_generator_function(secretfile)

    # create an experiment from generated instances
    setup_experiment = SetupAirQualityExperiment(experiment_dir, secretfile=secretfile)
    for instance in instance_list:
        setup_experiment.add_instance(instance)
    # download the data
    setup_experiment.load_datasets()
    # save the data and model params to file
    for instance in instance_list:
        setup_experiment.write_instance_to_file(instance.instance_id)

@app.command()
def run(experiment_name: ExperimentName, experiment_dir: Path = ExperimentDir) -> None:
    """Run an experiment: fit models and predict"""
    experiment_dir = experiment_dir / experiment_name.value
    runnable_experiment = RunnableAirQualityExperiment(experiment_dir)
    # TODO load instance ids


    runnable_experiment.load_datasets()
    runnable_experiment.run_experiment()

@app.command()
def batch(experiment_name: ExperimentName, batch_start: int, batch_size: int, experiment_dir: Path = ExperimentDir) -> None:
    """Run a batch of experiments"""
    # get the list of instances
    # only load instances from batch_start to (batch_size + batch_size)
    # run experiment with subset of instances
    raise NotImplementedError("Coming soon - run a batch of experiments")

@app.command()
def update(experiment_name: ExperimentName, experiment_dir: Path = ExperimentDir) -> None:
    """Update experiment results to database"""
    raise NotImplementedError("Coming soon")
