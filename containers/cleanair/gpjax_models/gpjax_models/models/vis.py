import pickle, csv
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
import matplotlib.pyplot as plt
import os
from stdata.vis.spacetime import SpaceTimeVisualise


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
    # test_laqn_true_values = true_y
    hexgrid_df = fix_df_columns(raw_data["test"]["hexgrid"]["df"])

    # Load results
    results = load_results(data_root)
    train_laqn_df["pred"] = results["predictions"]["train_laqn"]["mu"][0].T
    train_laqn_df["var"] = np.squeeze(results["predictions"]["train_laqn"]["var"][0])
    train_laqn_df["observed"] = train_laqn_df["NO2"]

    train_laqn_df["NO2"] = train_laqn_df["NO2"]

    test_laqn_df["pred"] = results["predictions"]["test_laqn"]["mu"][0].T
    test_laqn_df["var"] = np.squeeze(results["predictions"]["test_laqn"]["var"][0])
    test_laqn_df["observed"] = day_3_gt["NO2"]

    # train_laqn_df["pred"] = train_laqn_df["traffic"]
    # test_laqn_df["pred"] = test_laqn_df["traffic"]

    # train_laqn_df["measurement_start_utc"] = pd.to_datetime(
    #     train_laqn_df["measurement_start_utc"]
    # )
    train_end = train_laqn_df["epoch"].max()
    laqn_df = pd.concat([train_laqn_df, test_laqn_df])
    if False:
        #'geom' is the column containing Shapely Point geometries
        hexgrid_df["geom"] = gpd.points_from_xy(hexgrid_df["lon"], hexgrid_df["lat"])

        # Buffer each Point geometry by 0.002
        hexgrid_df["geom"] = hexgrid_df["geom"].apply(lambda point: point.buffer(0.002))

        # Create a GeoDataFrame using the 'geom' column
        hexgrid_gdf = gpd.GeoDataFrame(hexgrid_df, geometry="geom")
        hexgrid_df["pred"] = results["predictions"]["hexgrid"]["mu"][0].T
        # hexgrid_df["pred"] = hexgrid_df["traffic"]
        hexgrid_df["var"] = np.squeeze(results["predictions"]["hexgrid"]["var"][0])
    else:
        hexgrid_df = None

    sat_df = fix_df_columns(raw_data["train"]['sat']['df'])
    # TODO: NEED TO CHECK!! this should match is handling the satllite data
    sat_df = sat_df[['lon', 'lat', 'NO2', 'epoch', 'box_id']].groupby(['epoch', 'box_id']).mean().reset_index()
    # copy predictions 
    sat_df['pred'] = results["predictions"]['sat']['mu'][0]
    sat_df['var'] = results["predictions"]['sat']['var'][0]
    sat_df['observed'] = sat_df['NO2']

    laqn_df['residual'] =  laqn_df['observed'] - laqn_df['pred']
    laqn_df['pred'] = laqn_df['residual']

    vis_obj = SpaceTimeVisualise( laqn_df, hexgrid_df, sat_df=sat_df, geopandas_flag=True, test_start=train_end)
    #vis_obj = SpaceTimeVisualise( laqn_df, hexgrid_df, geopandas_flag=True, test_start=train_end)

    # Show the visualization
    vis_obj.show()
