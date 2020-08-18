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


def transform_datetime(
    time_df: pd.DataFrame,
    transformation: str = "hour",
    col: str = "measurement_start_utc",
    normalise_datetime: bool = False,
) -> pd.DataFrame:
    """
    Normalise a pandas datetime series with respect to (wrt) a time attribute.

    Args:
        time_df: Must have a datetime col to normalise.
    
    Keyword args:
        transformation: Name of the method for transforming datetime.
            Either epoch or hour.
        col: Name of the datetime column.
        normalise_datetime: If true, subtract the mean and divide by standard
            deviation of the time column.

    Returns:
        DataFrame with two new columns called 'time' and 'time_norm'.
    """
    transformed_df = time_df.copy()
    if transformation == "epoch":
        # use the datetime.timestamp() method to convert to integer
        transformed_df["time"] = transformed_df[col].apply(lambda x: x.timestamp())

    elif transformation == "hour":
        # take the hour of the day as the time column
        transformed_df["time"] = transformed_df[col].dt.hour

    else:
        raise ValueError(
            "wrt must be either hour or epoch. You passed {arg}".format(
                arg=transformation
            )
        )

    if normalise_datetime:
        transformed_df["time_norm"] = normalise(transformed_df["time"])

    transformed_df = transformed_df.sort_values("time")
    return transformed_df


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
