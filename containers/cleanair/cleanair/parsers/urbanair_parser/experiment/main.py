"""Setup, run and update experiments"""

from typing import Callable, List
from pathlib import Path
import typer
from ....experiment import (
    RunnableAirQualityExperiment,
    SetupAirQualityExperiment,
    generate_air_quality_experiment,
)
from ....mixins import InstanceMixin
from ..shared_args import ExperimentDir
from ..state import state
from ....types import ExperimentName
from .local import app as local_app

app = typer.Typer(help="Experiment CLI")

# Add local experiment cli to main experiment cli
app.add_typer(local_app, name="local")


@app.command()
def setup(
    experiment_name: ExperimentName, experiment_root: Path = ExperimentDir
) -> None:
    """Setup an experiment: load data + setup model parameters"""
    secretfile: str = state["secretfile"]

    # get the function that will generate instances
    experiment_generator_function: Callable[[str], List[InstanceMixin]] = getattr(
        generate_air_quality_experiment, experiment_name.value
    )
    # generate the instances
    instance_list = experiment_generator_function(secretfile)

    # create an experiment from generated instances
    setup_experiment = SetupAirQualityExperiment(
        experiment_name, experiment_root, secretfile=secretfile
    )
    for instance in instance_list:
        setup_experiment.add_instance(instance)
    # download the data
    setup_experiment.load_datasets()
    # save the data and model params to file
    for instance in instance_list:
        setup_experiment.write_instance_to_file(instance.instance_id)
    setup_experiment.write_experiment_config_to_json()


@app.command()
def run(experiment_name: ExperimentName, experiment_root: Path = ExperimentDir) -> None:
    """Run an experiment: fit models and predict"""
    # setup experiment
    runnable_experiment = RunnableAirQualityExperiment(experiment_name, experiment_root)

    # load instances from file
    experiment_config = runnable_experiment.read_experiment_config_from_json()
    runnable_experiment.add_instances_from_file(experiment_config.instance_id_list)

    # load datasets from file
    runnable_experiment.load_datasets()
    # run the experiment: train, predict and save results
    runnable_experiment.run_experiment()


@app.command()
def batch(
    experiment_name: ExperimentName,
    batch_start: int,
    batch_size: int,
    experiment_root: Path = ExperimentDir,
) -> None:
    """Run a batch of experiments"""
    # get the list of instances
    runnable_experiment = RunnableAirQualityExperiment(experiment_name, experiment_root)
    # only load instances from batch_start to (batch_size + batch_size)
    experiment_config = runnable_experiment.read_experiment_config_from_json()
    num_instances = len(experiment_config.instance_id_list)

    # raise error if invalid batch start
    if batch_start >= num_instances:
        raise ValueError(
            f"Number of instances in experiment is {num_instances}. You passed batch start of {batch_start}"
        )

    end_of_batch_index = min(batch_start + batch_size, num_instances)
    instance_id_batch = experiment_config.instance_id_list[
        batch_start:end_of_batch_index
    ]
    runnable_experiment.add_instances_from_file(instance_id_batch)

    # run experiment with subset of instances
    # load datasets from file
    runnable_experiment.load_datasets()
    # run the experiment: train, predict and save results
    runnable_experiment.run_experiment()


@app.command()
def update(
    experiment_name: ExperimentName, experiment_root: Path = ExperimentDir
) -> None:
    """Update experiment results to database"""
    raise NotImplementedError("Coming soon")
