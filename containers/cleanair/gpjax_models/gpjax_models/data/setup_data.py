import pickle
import numpy as np
import pandas as pd
from stdata.ops import ensure_continuous_timeseries
from stdata.utils import datetime_to_epoch


def get_data_file_names(fold):
    return {
        "raw": f"raw_data.pickle",
        "train": f"train_data.pickle",
        "test": f"test_data.pickle",
    }


def get_X(df):
    # return np.array(df[['epoch', 'lat', 'lon', 'value_100_total_a_road_length', 'value_100_total_a_road_primary_length', 'value_100_flat', 'value_100_max_canyon_ratio']])
    return np.array(
        df[["epoch", "lat", "lon", "value_200_total_a_road_primary_length"]]
    )


def get_Y(df):
    return np.array(df["NO2"])[:, None]


def get_Y_sat(df):
    # Sat has one value per box_id, so we only need to return the first one
    return np.array([df["NO2"].iloc[0]])[:, None]


def get_X_norm(df):
    return np.array(df[["epoch_norm", "lat_norm", "lon_norm", "value_200_park_norm"]])


def process_sat_data(train_data_sat):
    """process satellite to group by box id"""
    train_data_sat = train_data_sat.sort_values(by=["box_id", "lat", "lon"])

    sat_gb = train_data_sat.groupby(["box_id", "epoch"])
    sat_arr = [sat_gb.get_group(i) for i in sat_gb.groups]
    X_sat = np.array([get_X(df_i) for df_i in sat_arr])
    Y_sat = np.array([get_Y_sat(df_i) for df_i in sat_arr])

    Y_sat = Y_sat[..., 0]

    return X_sat, Y_sat


def process_data_test(df):
    return get_X_norm(df)


def process_data(df):
    return get_X(df), get_Y(df)


def clean_data(x_array, y_array):
    """Remove nans and missing data for use in GPflow

    Args:
        x_array: N x D numpy array,
        y_array: N x 1 numpy array

    Returns:
        x_array: Feature array cleaned of NaNs.
        y_array: Target array cleaned of NaNs
    """
    idx = ~np.isnan(y_array[:, 0])
    x_array = x_array[idx, :]
    y_array = y_array[idx, :]

    idx = np.isnan(x_array[:, :])
    idx = [not (True in row) for row in idx]
    x_array = x_array[idx, :]
    y_array = y_array[idx, :]

    return x_array, y_array


def time_norm(X, wrt_to_X):
    """units will now be in days"""
    return (X - np.min(wrt_to_X)) / (60 * 60 * 24)


def space_norm(X, wrt_X):
    df_norm = normalise(X[:, 1:3], wrt_X[:, 1:3])
    return df_norm[:, 0], df_norm[:, 1]


def normalise(X, wrt_X):
    return (X - np.mean(wrt_X, axis=0)) / np.std(wrt_X, axis=0)


def norm_X(X, wrt_X):
    """
    First column is epoch, second is lat, third is lon, the rest are covariates

    Epochs:
        convert units to days, and shift to start at zero

    lat/lon:
        z-standardised

    Covariates:
        z-standarised
    """
    X_time = time_norm(X[..., 0], wrt_X[..., 0])
    X_eastings, X_northings = space_norm(X, wrt_X)
    X_covariates = normalise(X[..., 3:], wrt_X[..., 3:])
    X_norm = np.hstack(
        [X_time[:, None], X_eastings[:, None], X_northings[:, None], X_covariates]
    )
    return X_norm


def generate_data(train_data, test_data):

    # Load dataframes
    train_laqn_df = train_data["laqn"]
    train_sat_df = train_data["satellite"]
    test_laqn_df = test_data["laqn"]
    test_hexgrid_df = test_data["hexgrid"]

    # Extract X and Y

    # collect training arrays
    train_laqn_X, train_laqn_Y = process_data(train_laqn_df)
    train_sat_X, train_sat_Y = process_sat_data(train_sat_df)

    # collect training arrays -- no Y available for testing data
    test_laqn_X = get_X(test_laqn_df)
    test_hexgrid_X = get_X(test_hexgrid_df)

    # Remove NaN data
    train_laqn_X, train_laqn_Y = clean_data(train_laqn_X, train_laqn_Y)
    train_sat_X, train_sat_Y = clean_data(train_sat_X, train_sat_Y)

    # Normalize X, laqn_X is used as the reference
    train_laqn_X_norm = norm_X(train_laqn_X, train_laqn_X)
    train_sat_X_norm_list = [
        norm_X(train_sat_X[i], train_laqn_X) for i in range(train_sat_X.shape[0])
    ]
    train_sat_X_norm = np.array(train_sat_X_norm_list)

    test_laqn_X_norm = norm_X(test_laqn_X, train_laqn_X)
    test_hexgrid_X_norm = norm_X(test_hexgrid_X, train_laqn_X)

    # check shapes
    print("======")
    print(
        f"LAQN train: {train_laqn_X_norm.shape}, {train_laqn_X.shape}, {train_laqn_Y.shape}"
    )
    print(
        f"SAT train: {train_sat_X_norm.shape}, {train_sat_X.shape}, {train_sat_Y.shape}"
    )
    print(f"LAQN test: {test_laqn_X_norm.shape}, {test_laqn_X.shape}, -")
    print(f"HEXGRID test: {test_hexgrid_X_norm.shape}, {test_hexgrid_X.shape}, -")
    print("======")

    # save data
    train_dict = {
        "laqn": {"X": train_laqn_X_norm, "Y": train_laqn_Y},
        "sat": {"X": train_sat_X_norm, "Y": train_sat_Y},
    }

    test_dict = {
        "laqn": {"X": test_laqn_X_norm, "Y": None},
        "hexgrid": {"X": test_hexgrid_X_norm, "Y": None},
    }

    meta_dict = {
        "train": {"laqn": {"df": train_laqn_df}, "sat": {"df": train_sat_df}},
        "test": {"laqn": {"df": test_laqn_df}, "hexgrid": {"df": test_hexgrid_df}},
    }

    with open("raw_data.pkl", "wb") as file:
        pickle.dump(meta_dict, file)
    return train_dict, test_dict
