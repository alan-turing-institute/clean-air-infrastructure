import pickle
import numpy as np
import pandas as pd
from nptyping import NDArray, Float64


from ..utils.file_manager import FileManager
from ..types.dataset_types import FeaturesDict
from .normalise import normalise, space_norm, time_norm


def get_data_file_names(fold):
    return {
        "raw": f"raw_data.pickle",
        "train": f"train_data.pickle",
    }


def get_X(df):
    return np.array(df[["epoch", "lat", "lon"]])


def get_Y(df):
    return np.array(df["NO2"])[:, None]


def process_data(df):
    return get_X(df), get_Y(df)


def norm_X(X: np.ndarray, wrt_X: np.ndarray) -> np.ndarray:
    X_time = time_norm(X[:, 0], wrt_X[:, 0])
    X_eastings, X_northings = space_norm(X, wrt_X)

    X_covariates = normalise(X[:, 3:], wrt_X[:, 3:])

    X_norm = np.hstack(
        [X_time[:, None], X_eastings[:, None], X_northings[:, None], X_covariates]
    )

    return X_norm


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
