import pickle, csv
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
import matplotlib.pyplot as plt
import os
from stdata.vis.spacetime import SpaceTimeVisualise
import geopandas as gpd
from stdata.utils import to_gdf

from pysal.explore import esda  # Exploratory Spatial analytics
from pysal.lib import weights  # Spatial weights

directory_path = Path('/Users/oliverhamelijnck/Downloads/dataset/')

# Create the directory if it doesn't exist
if not os.path.exists(directory_path):
    os.makedirs(directory_path)


def load_data(root):
    with open(
        str(
            directory_path / "training_dataset.pkl"
        ),
        "rb",
    ) as file:
        training_data = pd.read_pickle(file)
    with open(
        str(
            directory_path/ "test_dataset.pkl"
        ),
        "rb",
    ) as file:
        testing_data = pd.read_pickle(file)
    # Load raw data using pickle
    with open(
        directory_path / "raw_data_3.pkl",
        "rb",
    ) as file:
        raw_data = pd.read_pickle(file)

    with open(
        directory_path / "test_true_dataset.pkl",
        "rb",
    ) as file:
        true_y = pd.read_pickle(file)
    date_ranges = [
        ("2023-12-01 00:00:00+00:00", "2023-12-01 23:00:00+00:00"),
        ("2023-12-02 00:00:00+00:00", "2023-12-02 23:00:00+00:00"),
        ("2023-12-03 00:00:00+00:00", "2023-12-03 23:00:00+00:00"),
        ("2023-12-04 00:00:00+00:00", "2023-12-04 23:00:00+00:00"),
        ("2023-12-05 00:00:00+00:00", "2023-12-05 23:00:00+00:00"),
        ("2023-12-06 00:00:00+00:00", "2023-12-06 23:00:00+00:00"),
        ("2023-12-07 00:00:00+00:00", "2023-12-07 23:00:00+00:00"),
    ]

    # Convert the 'measurement_start_utc' column to datetime if it's not already
    true_y["laqn"]["measurement_start_utc"] = pd.to_datetime(
        true_y["laqn"]["measurement_start_utc"]
    )

    # Filter the laqn DataFrame for each specified date range
    filtered_data = []
    for start_date, end_date in date_ranges:
        day_gt = true_y["laqn"][
            (true_y["laqn"]["measurement_start_utc"] >= start_date)
            & (true_y["laqn"]["measurement_start_utc"] <= end_date)
        ]
        filtered_data.append(day_gt)

    # Assign each day's data to a separate variable for convenience
    day_1_gt, day_2_gt, day_3_gt, day_4_gt, day_5_gt, day_6_gt, day_7_gt = filtered_data

    return training_data, testing_data, raw_data, day_3_gt


def load_results(root):
    with open(
        str(root / "predictions_mrdgp_3.pkl"), "rb"
    ) as file:
        results = pd.read_pickle(file)
    return results


def fix_df_columns_dropna(df):
    df = df.rename(columns={"point_id": "id", "datetime": "measurement_start_utc"})
    return df.dropna(subset=["NO2"])


def fix_df_columns(df):
    return df.rename(columns={"point_id": "id", "datetime": "measurement_start_utc"})


if __name__ == "__main__":
    data_root = directory_path

    training_data, testing_data, raw_data, day_3_gt = load_data(data_root)
    day_3_gt = day_3_gt.reset_index(drop=True)
    train_laqn_df = fix_df_columns(raw_data["train"]["laqn"]["df"])
    test_laqn_df = fix_df_columns(raw_data["test"]["laqn"]["df"])
    true_val = fix_df_columns(day_3_gt)

    # Load results
    results = load_results(data_root)
    train_laqn_df["pred"] = results["predictions"]["train_laqn"]["mu"][0].T
    train_laqn_df["var"] = np.squeeze(results["predictions"]["train_laqn"]["var"][0])
    train_laqn_df["observed"] = train_laqn_df["NO2"]

    train_laqn_df["NO2"] = train_laqn_df["NO2"]

    test_laqn_df["pred"] = results["predictions"]["test_laqn"]["mu"][0].T
    test_laqn_df["var"] = np.squeeze(results["predictions"]["test_laqn"]["var"][0])
    test_laqn_df["observed"] = day_3_gt["NO2"]

    test_laqn_df['residual'] =  test_laqn_df['observed'] - test_laqn_df['pred']

    test_df = to_gdf(test_laqn_df[test_laqn_df['epoch']==test_laqn_df['epoch'].iloc[0]].copy())
    test_df = test_df[test_df['residual'].notna()].copy()

    # Generate W from the GeoDataFrame
    w = weights.distance.KNN.from_dataframe(test_df, k=8)
    # Row-standardization
    w.transform = "R"

    test_df["w_residual"] = weights.lag_spatial(w, test_df['residual'])

    test_df["residual_std"] = test_df["residual"] - test_df["residual"].mean()
    test_df["w_residual_std"] = weights.lag_spatial(w, test_df['residual_std'])

    lisa = esda.moran.Moran_Local(test_df['residual'], w)
    breakpoint()
