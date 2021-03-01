"""Setup, run and update experiments"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
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
from ....utils import FileManager
from ....visualisers import SpaceTimeVisualise

app = typer.Typer(help="Experiment CLI")

# Add local experiment cli to main experiment cli
local_app = typer.Typer(help="Experiment Local CLI")
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

def _load_hexgrid_polygons(hexgrid_df, hexgrid_path):
    #load hexgrid file
    hexgrid_file = pd.read_csv(hexgrid_path)
    hexgrid_file["geom"] = hexgrid_file["geom"].apply(wkt.loads)
    hexgrid_file = gpd.GeoDataFrame(hexgrid_file, geometry="geom")

    #convert hexgrid_df to geodataframe
    hexgrid_gdf = gpd.GeoDataFrame(
        hexgrid_df,
        geometry=gpd.points_from_xy(x=hexgrid_df.lat, y=hexgrid_df.lon)
    )

    #spatial join to match hexgrid_df with hexgrid polygon geoms
    grid_predictions = gpd.sjoin(hexgrid_gdf, hexgrid_file, how='right')
    grid_predictions['point_id'] = grid_predictions['point_id_x']


    return grid_predictions

def swap_lat_lon(df):
    df['_lat'] = df['lat']

    df['lat'] = df['lon']
    df['lon'] = df['_lat']
    return df.drop('_lat', axis=1)


@local_app.command()
def vis(experiment_name: ExperimentName, instance_id: str, experiment_root: Path, hexgrid: Path) -> None:
    """Visualise experiment results and predictions locally"""

    #load specific instance
    instance_path = Path(f'{experiment_root}/{experiment_name}/{instance_id}')
    file_manager = FileManager(instance_path)

    #load forecasts
    y_forecast = file_manager.load_forecast_from_pickle()
    y_train_forecast = file_manager.load_pred_training_from_pickle()



    #load input data
    X_forecast = file_manager.load_test_data()
    X_train_forecast = file_manager.load_training_data()

    _columns = ['point_id', 'epoch', 'lat', 'lon', 'measurement_start_utc']

    #prep training data
    laqn_train_df = X_train_forecast['laqn'][_columns]
    laqn_train_df['observed'] =  X_train_forecast['laqn']['NO2']
    laqn_train_df['pred'] = y_train_forecast['laqn']['NO2']['mean']
    laqn_train_df['var'] = y_train_forecast['laqn']['NO2']['var']

    hexgrid_train_df = None

    #prep test data
    laqn_test_df = X_forecast['laqn'][_columns]
    laqn_test_df['observed'] =  np.NaN
    laqn_test_df['pred'] = y_forecast['laqn']['NO2']['mean']
    laqn_test_df['var'] = y_forecast['laqn']['NO2']['var']

    hexgrid_test_df = X_forecast['hexgrid'][_columns]
    hexgrid_test_df = swap_lat_lon(hexgrid_test_df)
    hexgrid_test_df = _load_hexgrid_polygons(hexgrid_test_df, hexgrid)
    hexgrid_test_df['observed'] = np.NaN
    hexgrid_test_df['pred'] = y_forecast['hexgrid']['NO2']['mean']
    hexgrid_test_df['var'] = y_forecast['hexgrid']['NO2']['var']

    print('hexgrid_test_df: ', hexgrid_test_df.columns)
    hexgrid_test_df = hexgrid_test_df[_columns + ['geom', 'observed', 'pred', 'var']]

    laqn_df = pd.concat([laqn_train_df, laqn_test_df])
    laqn_df = swap_lat_lon(laqn_df)

    hexgrid_df = hexgrid_test_df


    #rename columns for spacetime.py
    laqn_df.columns = ['id', 'epoch', 'lon', 'lat', 'datetime', 'observed', 'pred', 'var']
    hexgrid_df.columns = ['id', 'epoch', 'lon', 'lat', 'datetime', 'geom', 'observed', 'pred', 'var']

    print(laqn_df['epoch'])
    print(hexgrid_df['epoch'])

    vis = SpaceTimeVisualise(laqn_df, hexgrid_df, geopandas_flag=True)
    vis.show()




@local_app.command()
def metrics(
    experiment_name: ExperimentName, instance_id: str, experiment_root: Path = ExperimentDir
) -> None:
    """Print local experiment metrics"""

    #TODO: ensure path, experiment_root, experiment_name are is correct format

    #load specific instance
    instance_path = Path(f'{experiment_root}/{experiment_name}/{instance_id}')
    file_manager = FileManager(instance_path)

    #load forecasts and true data
    y_forecast = file_manager.load_forecast_from_pickle()
    y_pred_training = file_manager.load_test_data()

    laqn_df = y_pred_training['laqn'][['measurement_start_utc'  ]]
    hexgrid_df = y_pred_training['laqn'][['measurement_start_utc']]

    #only computed metrics on laqn
    print(y_pred_training['laqn'][['measurement_start_utc', 'species_code']])

    #TODO: seems like the values on the test locations are stored locally?
    raise NotImplementedError()




