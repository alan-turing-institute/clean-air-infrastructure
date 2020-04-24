"""
Functions for normalising data ready for modelling.
"""

import numpy as np
import pandas as pd

def normalise(x):
    """Standardize all columns individually"""
    return (x - np.mean(x, axis=0)) / np.std(x, axis=0)

def denormalise(x, wrt_y):
    """Denormalize x given the original data it was standardized to"""
    return (x * np.std(wrt_y, axis=0)) + np.mean(wrt_y, axis=0)

def normalise_datetime(
    time_df: pd.DataFrame,
    wrt: str = "hour",
    col: str = "measurement_start_utc"
) -> pd.DataFrame:
    """
    Normalise a pandas datetime series with respect to (wrt) a time attribute.

    Args:
        time_df: Must have a datetime col to normalise.
        wrt (optional): Normalise with respect to hour or epoch.
        col (optional): Name of the datetime column.

    Returns:
        DataFrame with two new columns called 'time' and 'time_norm'.
    """
    if wrt == "epoch":
        time_df["time"] = time_df[col].astype('int64')//1e9 #convert to epoch
        time_df["time_norm"] = normalise(time_df["time"])

    elif wrt == "hour":
        time_df["time"] = time_df[col].dt.hour
        time_df["time_norm"] = (time_df["time"] - 12) / 12

    else:
        raise ValueError("wrt must be either hour or epoch. You passed {arg}".format(arg=wrt))

    return time_df

def normalise_location(space_df: pd.DataFrame, x_col="lon", y_col="lat") -> pd.DataFrame:
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
