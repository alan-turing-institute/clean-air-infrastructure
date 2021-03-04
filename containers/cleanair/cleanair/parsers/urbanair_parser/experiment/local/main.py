import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely import wkt
import uuid
import sklearn
import tabulate
from pathlib import Path
import typer
from typing import Optional
from .....types import ExperimentName, Source
from .....utils import FileManager
from .....visualisers import SpaceTimeVisualise
from .....models import ModelData
from ...state import state


app = typer.Typer(help="Experiment Local CLI")


def get_instance_ids(experiment_path):
    """Return all instance ids for a given experiment."""
    all_instance_ids = []

    for child in experiment_path.iterdir():
        if child.is_dir():
            all_instance_ids.append(child.name)

    return all_instance_ids


def compute_metrics(true_y, pred_y):
    """Compute multiple metrics.

    @TODO: should use air_quality_metrics_class for this
    """
    metrics = {
        "mse": sklearn.metrics.mean_squared_error,
        "rmse": lambda a, b: np.sqrt(sklearn.metrics.mean_squared_error(a, b)),
    }

    # ensure correct shape
    true_y = np.squeeze(true_y)
    pred_y = np.squeeze(pred_y)

    assert true_y.shape == pred_y.shape

    # remove nans
    non_nan_index = np.logical_not(np.isnan(true_y))

    true_y = true_y[non_nan_index]
    pred_y = pred_y[non_nan_index]

    results = {}
    for metric, metric_fn in metrics.items():
        results[metric] = metric_fn(true_y, pred_y)

    return results

def precompute_hexgrid_sjoin(file_manager, hexgrid_path):
    hexgrid_df = file_manager.load_test_data()["hexgrid"]
    y = file_manager.load_forecast_from_pickle()["hexgrid"]

    hexgrid_df = swap_lat_lon(hexgrid_df)

    # load hexgrid file
    hexgrid_file = pd.read_csv(hexgrid_path)
    hexgrid_file["geom"] = hexgrid_file["geom"].apply(wkt.loads)
    hexgrid_file = gpd.GeoDataFrame(hexgrid_file, geometry="geom")

    #use only one epoch
    hexgrid_df = hexgrid_df[hexgrid_df['measurement_start_utc'] == hexgrid_df['measurement_start_utc'][0]]

    # convert hexgrid_df to geodataframe
    hexgrid_gdf = gpd.GeoDataFrame(
        hexgrid_df, geometry=gpd.points_from_xy(x=hexgrid_df.lat, y=hexgrid_df.lon)
    )


    # spatial join to match hexgrid_df with hexgrid polygon geoms
    grid_predictions = gpd.sjoin(hexgrid_gdf, hexgrid_file, how="right")
    grid_predictions["point_id"] = grid_predictions["point_id_x"]

    grid_predictions = grid_predictions[['point_id', 'geom']]

    grid_predictions.to_csv('~/Downloads/hexgrid.csv', index=False)

    exit()

def load_hexgrid_polygons(hexgrid_df, hexgrid_path):
    # load hexgrid file
    hexgrid_file = pd.read_csv(hexgrid_path)
    hexgrid_file["geom"] = hexgrid_file["geom"].apply(wkt.loads)
    hexgrid_file = gpd.GeoDataFrame(hexgrid_file, geometry="geom")

    # convert hexgrid_df to geodataframe
    hexgrid_gdf = gpd.GeoDataFrame(
        hexgrid_df, geometry=gpd.points_from_xy(x=hexgrid_df.lat, y=hexgrid_df.lon)
    )

    # spatial join to match hexgrid_df with hexgrid polygon geoms
    grid_predictions = gpd.sjoin(hexgrid_gdf, hexgrid_file, how="right")
    grid_predictions["point_id"] = grid_predictions["point_id_x"]

    return grid_predictions


def swap_lat_lon(df):
    df["_lat"] = df["lat"]

    df["lat"] = df["lon"]
    df["lon"] = df["_lat"]
    return df.drop("_lat", axis=1)


def get_laqn_forecast_with_observations(instance, file_manager, model_data):
    X_forecast = file_manager.load_test_data()["laqn"]

    # download forecast observations
    laqn_forecast_true = model_data.download_forecast_source_data(
        full_config=instance.data_config, source=Source.laqn
    )


    laqn_forecast_true = laqn_forecast_true[
        ["point_id", "measurement_start_utc", "NO2"]
    ]

    # load forecast predictions
    y_forecast = file_manager.load_forecast_from_pickle()["laqn"]["NO2"]
    X_forecast["NO2_mean"] = y_forecast["mean"]
    X_forecast["NO2_var"] = y_forecast["var"]

    # combine true and predictions
    laqn_forecast = X_forecast.merge(
        laqn_forecast_true, on=["point_id", "measurement_start_utc"], how="inner"
    )

    laqn_forecast["pred"] = laqn_forecast["NO2_mean"]
    laqn_forecast["var"] = laqn_forecast["NO2_var"]
    laqn_forecast["observed"] = laqn_forecast["NO2"]

    return laqn_forecast

def get_laqn_forecast(instance, file_manager, model_data):
    X_forecast = file_manager.load_test_data()["laqn"]

 
    # load forecast predictions
    y_forecast = file_manager.load_forecast_from_pickle()["laqn"]["NO2"]
    X_forecast["NO2_mean"] = y_forecast["mean"]
    X_forecast["NO2_var"] = y_forecast["var"]


    X_forecast["pred"] = X_forecast["NO2_mean"]
    X_forecast["var"] = X_forecast["NO2_var"]
    X_forecast["observed"] = np.NaN

    return X_forecast



def get_laqn_train_with_observations(file_manager):
    # already has NO2
    X = file_manager.load_training_data()["laqn"]

    # load forecast predictions
    y = file_manager.load_pred_training_from_pickle()["laqn"]["NO2"]
    X["NO2_mean"] = y["mean"]
    X["NO2_var"] = y["var"]

    X["observed"] = X["NO2"]
    X["pred"] = X["NO2_mean"]
    X["var"] = X["NO2_var"]

    return X

def get_satellite_train_with_observations(file_manager):
    # already has NO2
    X = file_manager.load_training_data()["satellite"]

    # load forecast predictions
    X["NO2_mean"] = np.NaN
    X["NO2_var"] = np.NaN

    X["observed"] = X["NO2"]
    X["pred"] = np.NaN
    X["var"] = np.NaN

    return X



def get_hexgrid_forecast(file_manager, hexgrid_file):
    hexgrid_df = file_manager.load_test_data()["hexgrid"]
    y = file_manager.load_forecast_from_pickle()["hexgrid"]

    hexgrid_df = swap_lat_lon(hexgrid_df)

    hexgrid_df = load_hexgrid_polygons(hexgrid_df, hexgrid_file)

    hexgrid_df["observed"] = np.NaN
    hexgrid_df["pred"] = y["NO2"]["mean"]
    hexgrid_df["var"] = y["NO2"]["var"]

    return hexgrid_df

def get_hexgrid_forecast_no_sjoin(file_manager, hexgrid_file):
    hexgrid_df = file_manager.load_test_data()["hexgrid"]
    y = file_manager.load_forecast_from_pickle()["hexgrid"]
    hexgrid_df = swap_lat_lon(hexgrid_df)

    # load hexgrid file
    hexgrid_file = pd.read_csv(hexgrid_file)
    hexgrid_file["geom"] = hexgrid_file["geom"].apply(wkt.loads)
    hexgrid_file['point_id'] = hexgrid_file['point_id'].apply(uuid.UUID)

    hexgrid_df = hexgrid_df.merge(hexgrid_file, on='point_id', how='left')

    hexgrid_df = gpd.GeoDataFrame(hexgrid_df, geometry="geom")

    hexgrid_df["observed"] = np.NaN
    hexgrid_df["pred"] = y["NO2"]["mean"]
    hexgrid_df["var"] = y["NO2"]["var"]

    return hexgrid_df


def check_if_can_plot_hexgrid(file_manager, hexgrid_file):
    """Rudimentary check to see if hexgrid should be plotted or not."""
    return (
        "hexgrid" in file_manager.load_forecast_from_pickle().keys()
    ) and hexgrid_file is not None

def check_if_can_plot_satellite(file_manager):
    return (
        "satellite" in file_manager.load_training_data().keys()
    ) 

@app.command()
def vis(
    experiment_name: ExperimentName,
    instance_id: str,
    experiment_root: Path,
    hexgrid: Optional[Path] = None,
    test_observations: Optional[bool]=True,
    spatial_join: Optional[bool]=False
) -> None:
    """Visualise experiment results and predictions locally"""

    # load specific instance
    instance_path = Path(f"{experiment_root}/{experiment_name}/{instance_id}")
    file_manager = FileManager(instance_path)
    instance = file_manager.read_instance_from_json()
    secretfile = state["secretfile"]
    model_data = ModelData(secretfile=secretfile)

    #precompute_hexgrid_sjoin(file_manager, hexgrid)

    plot_hexgrid_flag = check_if_can_plot_hexgrid(file_manager, hexgrid)
    plot_sat_flag = check_if_can_plot_satellite(file_manager)

    _columns = ["point_id", "epoch", "lat", "lon", "measurement_start_utc"]

    # load LAQN data
    print('load laqn_train')
    laqn_train_df = get_laqn_train_with_observations(file_manager)

    if test_observations:
        print('downloading test_observations')
        laqn_test_df = get_laqn_forecast_with_observations(
            instance, file_manager, model_data
        )
    else:
        print('no test_observations')
        laqn_test_df = get_laqn_forecast(
            instance, file_manager, model_data
        )

    laqn_train_df = laqn_train_df[_columns + ["observed", "pred", "var"]]
    laqn_test_df = laqn_test_df[_columns + ["observed", "pred", "var"]]

    if plot_sat_flag:
        sat_df = get_satellite_train_with_observations(file_manager)
        sat_df = sat_df[_columns + ["observed", "pred", "var"]]
    else:
        sat_df = None



    # load hexgrid if in test data
    if plot_hexgrid_flag:
        print('loading hexgrid')
        if spatial_join:
            hexgrid_df = get_hexgrid_forecast(file_manager, hexgrid)
            hexgrid_df = hexgrid_df[_columns + ["geom", "observed", "pred", "var"]]

        else:
            hexgrid_df = get_hexgrid_forecast_no_sjoin(file_manager, hexgrid)
            hexgrid_df = hexgrid_df[_columns + ["geom", "observed", "pred", "var"]]
    else:
        print('no hexgrid')
        hexgrid_df = None

    laqn_df = pd.concat([laqn_train_df, laqn_test_df])
    # laqn_df = laqn_test_df
    laqn_df = swap_lat_lon(laqn_df)

    # rename columns for spacetime.py
    laqn_df.columns = [
        "id",
        "epoch",
        "lon",
        "lat",
        "datetime",
        "observed",
        "pred",
        "var",
    ]
    if plot_hexgrid_flag:
        hexgrid_df.columns = [
            "id",
            "epoch",
            "lon",
            "lat",
            "datetime",
            "geom",
            "observed",
            "pred",
            "var",
        ]

    vis = SpaceTimeVisualise(
        laqn_df,
        hexgrid_df,
        sat_df=sat_df,
        geopandas_flag=True,
        test_start=np.min(laqn_test_df["epoch"]),
    )
    vis.show()


@app.command()
def metrics(
    experiment_name: ExperimentName,
    experiment_root: Path,
    instance_id: Optional[str] = None,
) -> None:
    """Print local experiment metrics.
    If instance_id is supplied then will print metrics for that specific instance.
    Otherwise it will print metrics across all instances.
    """
    experiment_path = Path(f"{experiment_root}/{experiment_name}/")

    # If instance_id is not passes load all instance ids for experiment
    all_instance_ids = []

    if instance_id is None:
        all_instance_ids = get_instance_ids(experiment_path)
    else:
        # load specific instance
        all_instance_ids.append(instance_id)

    debug = False

    meta = {}
    results = {}
    for instance_id in all_instance_ids:
        try:

            instance_path = Path(f"{experiment_root}/{experiment_name}/{instance_id}")
            file_manager = FileManager(instance_path)
            instance = file_manager.read_instance_from_json()
            secretfile = state["secretfile"]

            if debug:
                results[instance_id] = {'rmse': 1.0, 'mse': 1.0}

            else:
                model_data = ModelData(secretfile=secretfile)

                # get predictions and true data
                laqn_forecast = get_laqn_forecast_with_observations(
                    instance, file_manager, model_data
                )

                # compute metric
                true_y = np.array(laqn_forecast["NO2"])
                pred_y = np.array(laqn_forecast["NO2_mean"])

                results[instance_id] = compute_metrics(true_y, pred_y)

            #meta info
            meta[instance_id] = {}
            meta[instance_id]['static_features'] = [str(s) for s in instance.data_config.static_features]
        except Exception as e:
            print(f'Error with instance: {instance_id} -- ignoring!')
            print(e)
            continue



    # Print Table of Results
    results_df = pd.DataFrame(results).T
    metrics = list(results_df.columns)


    meta_df = pd.DataFrame(meta).T
    meta = list(meta_df.columns)

    results_df = results_df.merge(meta_df, left_index=True, right_index=True)

    print(tabulate.tabulate(results_df, headers=["Instance Id"] + metrics + meta))
