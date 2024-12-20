"""
Functions for normalising data ready for modelling.
"""

import numpy as np
import pandas as pd


def normalise(X, wrt_X):
    return (X - np.mean(wrt_X, axis=0)) / np.std(wrt_X, axis=0)


def denormalise(x, wrt_y):
    """Denormalize x given the original data it was standardized to"""
    return (x * np.std(wrt_y, axis=0)) + np.mean(wrt_y, axis=0)


def space_norm(X, wrt_X):
    df_norm = normalise(X[:, 1:3], wrt_X[:, 1:3])
    return df_norm[:, 0], df_norm[:, 1]


def time_norm(X, wrt_to_X):
    """units will now be in days"""
    return (X - np.min(wrt_to_X)) / (60 * 60 * 24)


def normalise_datetime(
    time_df: pd.DataFrame, wrt: str = "hour", col: str = "measurement_start_utc"
) -> pd.DataFrame:
    """
    Normalise a pandas datetime series with respect to (wrt) a time attribute.

    Args:
        time_df: Must have a datetime col to normalise.
        wrt (optional): Normalise with respect to 'clipped_hour', 'hour' or 'epoch'.
        col (optional): Name of the datetime column.

    Returns:
        DataFrame with two new columns called 'time' and 'time_norm'.
    """
    if wrt == "epoch":
        time_df["time"] = time_df[col].astype("int64") // 1e9  # convert to epoch
        time_df["time_norm"] = normalise(time_df["time"], time_df["time"])

    elif wrt == "clipped_hour":
        time_df["time"] = time_df[col].dt.hour
        time_df["time_norm"] = (time_df["time"] - 12) / 12

    elif wrt == "hour":
        time_df["time"] = time_df[col].dt.hour
        time_df["time_norm"] = time_df["time"]

    else:
        raise ValueError(
            "wrt must be either hour or epoch. You passed {arg}".format(arg=wrt)
        )

    time_df = time_df.sort_values("time_norm")
    return time_df


def normalise_location(
    space_df: pd.DataFrame, x_col="lon", y_col="lat"
) -> pd.DataFrame:
    """
    Normalise the location columns of a pandas dataframe.

    Args:
        space_df: Must have two spatial columns to normalise.
        x_col: The name of the column on the x spatial axis.
        y_col: The name of the column on the y spatial axis.

    Returns:
        space_df with two new columsn called lon_norm and lat_norm.
    """
    space_df[x_col + "_norm"] = normalise(space_df[x_col])
    space_df[y_col + "_norm"] = normalise(space_df[y_col])
    return space_df
