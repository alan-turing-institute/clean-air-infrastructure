"""Setup, run and update experiments"""

from typing import Callable, List
from pathlib import Path
import typer
from ....experiment import RunnableAirQualityExperiment, SetupAirQualityExperiment, generate_air_quality_experiment
from ....mixins import InstanceMixin
from ..shared_args import ExperimentDir
from ..state import state
from ....types import ExperimentConfig, ExperimentName

app = typer.Typer(help="Experiment CLI")


@app.command()
def setup(experiment_name: ExperimentName, experiment_root: Path = ExperimentDir) -> None:
    """Setup an experiment: load data + setup model parameters"""
    secretfile: str = state["secretfile"]

    # get the function that will generate instances
    experiment_generator_function: Callable[str, List[InstanceMixin]] = getattr(
        generate_air_quality_experiment, experiment_name.value
    )
    # generate the instances
    instance_list = experiment_generator_function(secretfile)

    # create an experiment from generated instances
    setup_experiment = SetupAirQualityExperiment(experiment_name, experiment_root, secretfile=secretfile)
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
    for instance_id in experiment_config.instance_id_list:
        instance = runnable_experiment.get_file_manager(instance_id).load_instance_from_json()
        runnable_experiment.add_instance(instance)
    # load datasets from file
    runnable_experiment.load_datasets()
    # run the experiment: train, predict and save results
    runnable_experiment.run_experiment()

@app.command()
def batch(experiment_name: ExperimentName, batch_start: int, batch_size: int, experiment_root: Path = ExperimentDir) -> None:
    """Run a batch of experiments"""
    # get the list of instances
    # only load instances from batch_start to (batch_size + batch_size)
    # run experiment with subset of instances
    raise NotImplementedError("Coming soon - run a batch of experiments")

@app.command()
def update(experiment_name: ExperimentName, experiment_root: Path = ExperimentDir) -> None:
    """Update experiment results to database"""
    raise NotImplementedError("Coming soon")
