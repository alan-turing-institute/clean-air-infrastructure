import pickle
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
import os
import stdata
from stdata.vis.spacetime import SpaceTimeVisualise


directory_path = "containers/cleanair/gpjax_models/mrdgp_results"

# Create the directory if it doesn't exist
if not os.path.exists(directory_path):
    os.makedirs(directory_path)


def load_data(root):
    training_data = pickle.load(open(str(root / "train_data.pickle"), "rb"))
    testing_data = pickle.load(open(str(root / "test_data.pickle"), "rb"))
    raw_data = pd.read_pickle(
        "/Users/suedaciftci/projects/clean-air/clean-air-infrastructure/containers/cleanair/gpjax_models/data/raw_data.pickle"
    )

    return training_data, testing_data, raw_data


def load_results(root):
    training_data = pickle.load(
        open(
            str(root / "mrdgp_results" / "predictions_mrdgp.pkl"),
            "rb",
        )
    )
    return training_data


def fix_df_columns(df):
    return df.rename(columns={"point_id": "id", "datetime": "measurement_start_utc"})


if __name__ == "__main__":
    data_root = Path("containers/cleanair/gpjax_models/data")

    training_data, testing_data, raw_data = load_data(data_root)

    train_laqn_df = fix_df_columns(raw_data["train"]["laqn"]["df"])
    test_laqn_df = fix_df_columns(raw_data["test"]["laqn"]["df"])

    hexgrid_df = fix_df_columns(raw_data["test"]["hexgrid"]["df"])

    # Load results
    results = load_results(data_root)

    train_laqn_df["pred"] = results["predictions"]["train_laqn"]["mu"][0]
    train_laqn_df["var"] = results["predictions"]["train_laqn"]["var"][0]
    train_laqn_df["observed"] = train_laqn_df["NO2"]

    test_laqn_df["pred"] = results["predictions"]["test_laqn"]["mu"][0]
    test_laqn_df["var"] = results["predictions"]["test_laqn"]["var"][0]
    test_laqn_df["observed"] = np.NaN

    laqn_df = pd.concat([train_laqn_df, test_laqn_df])

    hexgrid_df = gpd.GeoDataFrame(
        hexgrid_df, geometry=gpd.points_from_xy(hexgrid_df["lon"], hexgrid_df["lat"])
    )
    hexgrid_df["geom"] = hexgrid_df["geometry"].buffer(0.002)

    hexgrid_df["pred"] = results["predictions"]["hexgrid"]["mu"][0]
    hexgrid_df["var"] = results["predictions"]["hexgrid"]["var"][0]
    # Create a SpaceTimeVisualise object with geopandas_flag=True
    vis_obj = SpaceTimeVisualise(laqn_df, hexgrid_df, geopandas_flag=True)

    # Show the visualization
    vis_obj.show()
