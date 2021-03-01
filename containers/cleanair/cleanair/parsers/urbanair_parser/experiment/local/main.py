import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import wkt
import uuid
import sklearn

from pathlib import Path
import typer
from ...shared_args import ExperimentDir
from .....types import ExperimentName, Source
from .....utils import FileManager
from .....visualisers import SpaceTimeVisualise
from .....models import ModelData
from ...state import state


app = typer.Typer(help="Experiment Local CLI")


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


@app.command()
def vis(
    experiment_name: ExperimentName,
    instance_id: str,
    experiment_root: Path,
    hexgrid: Path,
) -> None:
    """Visualise experiment results and predictions locally"""

    # load specific instance
    instance_path = Path(f"{experiment_root}/{experiment_name}/{instance_id}")
    file_manager = FileManager(instance_path)
    instance = file_manager.read_instance_from_json()
    secretfile = state["secretfile"]
    model_data = ModelData(secretfile=secretfile)

    #download forecast observations
    laqn_forecast_true = model_data.download_forecast_data_for_source(
        full_config=instance.data_config,
        source=Source.laqn
    )
    laqn_forecast_true = laqn_forecast_true[['point_id', 'measurement_start_utc', 'NO2']]

    # load forecasts
    y_forecast = file_manager.load_forecast_from_pickle()
    y_train_forecast = file_manager.load_pred_training_from_pickle()

    # load input data
    X_forecast = file_manager.load_test_data()
    X_train_forecast = file_manager.load_training_data()


    laqn_forecast = file_manager.load_forecast_from_csv("laqn")
    laqn_forecast["point_id"] = laqn_forecast["point_id"].apply(uuid.UUID)
    laqn_forecast["measurement_start_utc"] = pd.to_datetime(laqn_forecast["measurement_start_utc"])

    laqn_forecast = laqn_forecast.merge(laqn_forecast_true, on=['point_id', 'measurement_start_utc'], how='inner')

    _columns = ["point_id", "epoch", "lat", "lon", "measurement_start_utc"]

    # prep training data
    laqn_train_df = X_train_forecast["laqn"][_columns]
    laqn_train_df["observed"] = X_train_forecast["laqn"]["NO2"]
    laqn_train_df["pred"] = y_train_forecast["laqn"]["NO2"]["mean"]
    laqn_train_df["var"] = y_train_forecast["laqn"]["NO2"]["var"]

    # prep test data
    laqn_test_df = laqn_forecast[_columns]
    laqn_test_df["observed"] = laqn_forecast['NO2']
    laqn_test_df["pred"] = laqn_forecast["NO2_mean"]
    laqn_test_df["var"] = laqn_forecast["NO2_var"]

    hexgrid_test_df = X_forecast["hexgrid"][_columns]
    hexgrid_test_df = swap_lat_lon(hexgrid_test_df)
    hexgrid_test_df = load_hexgrid_polygons(hexgrid_test_df, hexgrid)
    hexgrid_test_df["observed"] = np.NaN
    hexgrid_test_df["pred"] = y_forecast["hexgrid"]["NO2"]["mean"]
    hexgrid_test_df["var"] = y_forecast["hexgrid"]["NO2"]["var"]

    print("hexgrid_test_df: ", hexgrid_test_df.columns)
    hexgrid_test_df = hexgrid_test_df[_columns + ["geom", "observed", "pred", "var"]]

    laqn_df = pd.concat([laqn_train_df, laqn_test_df])
    #laqn_df = laqn_test_df
    laqn_df = swap_lat_lon(laqn_df)

    hexgrid_df = hexgrid_test_df

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

    print(laqn_df["epoch"])
    print(hexgrid_df["epoch"])

    vis = SpaceTimeVisualise(laqn_df, hexgrid_df, geopandas_flag=True, test_start=np.min(laqn_test_df['epoch']))
    vis.show()


@app.command()
def metrics(
    experiment_name: ExperimentName,
    instance_id: str,
    experiment_root: Path
) -> None:
    """Print local experiment metrics"""

    # load specific instance
    instance_path = Path(f"{experiment_root}/{experiment_name}/{instance_id}")
    file_manager = FileManager(instance_path)
    instance = file_manager.read_instance_from_json()
    secretfile = state["secretfile"]
    model_data = ModelData(secretfile=secretfile)

    #download forecast observations
    laqn_forecast_true = model_data.download_forecast_data_for_source(
        full_config=instance.data_config,
        source=Source.laqn
    )
    laqn_forecast_true = laqn_forecast_true[['point_id', 'measurement_start_utc', 'NO2']]

    laqn_forecast = file_manager.load_forecast_from_csv("laqn")
    laqn_forecast["point_id"] = laqn_forecast["point_id"].apply(uuid.UUID)
    laqn_forecast["measurement_start_utc"] = pd.to_datetime(laqn_forecast["measurement_start_utc"])

    laqn_forecast = laqn_forecast.merge(laqn_forecast_true, on=['point_id', 'measurement_start_utc'], how='inner')

    #remove nans
    laqn_forecast = laqn_forecast[~pd.isnull(laqn_forecast['NO2'])]

    true_y = np.squeeze(np.array(laqn_forecast['NO2']))
    pred_y =  np.squeeze(np.array(laqn_forecast['NO2_mean']))

    mse = sklearn.metrics.mean_squared_error(true_y, pred_y)
    rmse = np.sqrt(mse)

    print(mse, rmse)



