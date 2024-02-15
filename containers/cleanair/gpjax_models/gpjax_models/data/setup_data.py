import pickle
import numpy as np
import pandas as pd
from pathlib import Path


from ..utils.file_manager import FileManager
from ..types.dataset_types import FeaturesDict
from .normalise import normalise, space_norm, time_norm


def get_data_file_names(fold):
    return {
        "raw": f"raw_data.pickle",
        "train": f"train_data.pickle",
        "test": f"test_data.pickle",
    }


def get_X(df):
    return np.array(df[["epoch", "lat", "lon", "value_200_park"]])


def get_X_norm(df):
    return np.array(df[["epoch_norm", "lat_norm", "lon_norm", "value_200_park_norm"]])


def get_Y(df):
    return np.array(df["NO2"])[:, None]


def get_Y_sat(df):
    # Sat has one value per box_id, so we only need to return the first one
    return np.array([df["NO2"].iloc[0]])[:, None]


def get_Y_norm(df):
    return np.array(df["NO2"])[:, None]


def get_Y_sat_norm(df):
    # Sat has one value per box_id, so we only need to return the first one
    return np.array([df["NO2"].iloc[0]])[:, None]


def process_data(df):
    return get_X(df), get_Y(df)


def process_data_test(df):
    return get_X_norm(df)


def process_data_norm(df):
    return get_X_norm(df), get_Y_norm(df)


def process_sat_data(train_data_sat):
    """process satellite to group by box id"""
    train_data_sat = train_data_sat.sort_values(by=["box_id", "lat", "lon"])

    sat_gb = train_data_sat.groupby(["box_id", "epoch"])
    sat_arr = [sat_gb.get_group(i) for i in sat_gb.groups]
    X_sat = np.array([get_X(df_i) for df_i in sat_arr])
    Y_sat = np.array([get_Y_sat(df_i) for df_i in sat_arr])

    Y_sat = Y_sat[..., 0]

    return X_sat, Y_sat


def time_norm(X, wrt_to_X):
    """units will now be in days"""
    return (X - np.min(wrt_to_X)) / (60 * 60 * 24)


def normalise(X, wrt_X):
    return (X - np.mean(wrt_X, axis=0)) / np.std(wrt_X, axis=0)


def space_norm(X, wrt_X):
    df_norm = normalise(X[:, 1:3], wrt_X[:, 1:3])
    return df_norm[:, 0], df_norm[:, 1]


def norm_X(X: np.ndarray, wrt_X: np.ndarray) -> np.ndarray:
    """
    First column is epoch, second is lat, third is lon, the rest are covariates

    Epochs:
        convert units to days, and shift to start at zero

    lat/lon:
        convert units to kilometers, and shift to start at zero

    Covariates:
        z-standarised
    """

    X_time = time_norm(X[:, 0], wrt_X[:, 0])
    X_eastings, X_northings = space_norm(X, wrt_X)

    X_covariates = normalise(X[:, 3:], wrt_X[:, 3:])

    X_norm = np.hstack(
        [X_time[:, None], X_eastings[:, None], X_northings[:, None], X_covariates]
    )

    return X_norm


def load_test_data(fnames, data_root: Path) -> dict:
    return pickle.load(open(data_root / fnames["test"], "rb"))


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


def generate_data(df):
    # load cleaned data pickle
    # collect training arrays
    train_X, train_Y = process_data(df)
    # Normalize X, laqn_X is used as the reference
    train_X_norm = norm_X(train_X, train_X)
    x_train, y_train = clean_data(train_X_norm, train_Y)

    # Create the train_dict
    train_dict = {
        "X": x_train,
        "Y": y_train,
    }

    return train_dict


def generate_data_norm(df):
    # load cleaned data pickle
    # collect training arrays
    train_X, train_Y = process_data_norm(df)

    # Create the train_dict
    train_dict = {
        "X": train_X,
        "Y": train_Y,
    }

    return train_dict


def generate_data_test(df):
    # load cleaned data pickle
    # collect training arrays
    test_X = process_data_test(df)

    # Create the train_dict
    test_dict = {"X": test_X, "Y": None}

    return test_dict
