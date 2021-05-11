"""Setup, run and update experiments"""

import logging
from typing import Callable, List, Optional
from pathlib import Path
import typer
from ....databases.queries import AirQualityInstanceQuery
from ....experiment import (
    ExperimentMixin,
    RunnableAirQualityExperiment,
    SetupAirQualityExperiment,
    UpdateAirQualityExperiment,
    generate_air_quality_experiment,
)
from ....metrics import AirQualityMetrics
from ....mixins import InstanceMixin
from ....models import ModelData
from ..shared_args import ExperimentDir
from ..state import state
from ....types import ExperimentName

app = typer.Typer(help="Experiment CLI")


@app.command()
def size(experiment_name: ExperimentName, experiment_root: Path = ExperimentDir) -> int:
    """Number of instances in experiment is the size"""
    logging.disable(logging.CRITICAL)  # turn off logging
    size_experiment = ExperimentMixin(experiment_name, experiment_root)
    experiment_config = size_experiment.read_experiment_config_from_json()
    size_experiment.add_instances_from_file(experiment_config.instance_id_list)
    print(size_experiment.get_num_instances())


@app.command()
def setup(
    experiment_name: ExperimentName,
    experiment_root: Path = ExperimentDir,
    use_cache: Optional[bool] = False,
    instance_root: Optional[Path] = None,
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
    if use_cache:
        setup_experiment.load_datasets_from_cache(instance_root)
    else:
        setup_experiment.load_datasets()
    # save the data and model params to file
    for instance in instance_list:
        setup_experiment.write_instance_to_file(instance.instance_id)
    setup_experiment.write_experiment_config_to_json()


@app.command()
def setup_cached_instance(cached_root: Path):
    """Setups an instance with all sources and all features."""

    setup(ExperimentName.cached_instance, cached_root)


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
    secretfile: str = state["secretfile"]
    update_experiment = UpdateAirQualityExperiment(
        experiment_name, experiment_root, secretfile=secretfile
    )
    experiment_config = update_experiment.read_experiment_config_from_json()
    update_experiment.add_instances_from_file(experiment_config.instance_id_list)
    update_experiment.update_remote_tables()
    update_experiment.update_result_tables()

@app.command()
def recent(limit: int) -> None:
    """Get the most recent instances"""
    secretfile: str = state["secretfile"]
    query = AirQualityInstanceQuery(secretfile)
    tabular = query.most_recent_instances(limit, output_type="tabulate")
    print(tabular)

@app.command()
def metrics(
    experiment_name: ExperimentName, experiment_root: Path = ExperimentDir
) -> None:
    """Update the metrics for the experiment"""
    secretfile: str = state["secretfile"]
    metrics_experiment = UpdateAirQualityExperiment(
        experiment_name, experiment_root, secretfile=secretfile
    )
    experiment_config = metrics_experiment.read_experiment_config_from_json()
    metrics_experiment.add_instances_from_file(experiment_config.instance_id_list)
    model_data = ModelData(secretfile=secretfile)

    for instance_id in metrics_experiment.get_instance_ids():
        instance_metrics = AirQualityMetrics(
            instance_id, secretfile=secretfile, connection=model_data.dbcnxn.connection
        )
        observation_df = instance_metrics.load_observation_df(model_data)
        result_df = instance_metrics.load_result_df()
        instance_metrics.evaluate_spatial_metrics(observation_df, result_df)
        instance_metrics.evaluate_temporal_metrics(observation_df, result_df)
        instance_metrics.update_remote_tables()
