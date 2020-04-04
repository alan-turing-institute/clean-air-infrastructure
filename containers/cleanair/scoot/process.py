"""
For data cleaning and processing.
"""

import numpy as np
import pandas as pd

def normalise(x):
    """Standardize all columns individually"""
    return (x - np.mean(x, axis=0)) / np.std(x, axis=0)

def denormalise(x, wrt_y):
    """Denormalize x given the original data it was standardized to"""
    return ( x * np.std(wrt_y, axis=0) ) + np.mean(wrt_y, axis=0)

def clean_and_normalise_df(df: pd.DataFrame):
    """Normalise lat, lon, epoch."""
    df['measurement_start_utc'] = pd.to_datetime(df['measurement_start_utc'])
    df['weekday'] = df['measurement_start_utc'].dt.dayofweek
    df['weekend'] = (df.weekday // 5 == 1).astype(float)
    df['epoch'] = df['measurement_start_utc'].astype('int64')//1e9 #convert to epoch
    df['epoch_norm'] = normalise(df['epoch'])
    df['lat_norm'] = normalise(df['lat'])
    df['lon_norm'] = normalise(df['lon'])
    return df

def filter_df(df: pd.DataFrame, detector_list: list, start: str, end: str):
    """
    Return a dataframe that only contains sensors in the list
    and only contains observations between the start and end datetime.
    """
    return df.loc[
        (df['detector_id'].isin(detector_list)) &
        (df["measurement_start_utc"] >= start) &
        (df["measurement_start_utc"] < end)
    ]

def split_df_into_numpy_array(
    df,
    detector_list,
    x_cols=['epoch_norm', 'lon_norm', 'lat_norm'],
    y_cols=["n_vehicles_in_interval"]
):
    """Returns list of X numpys and Y numpys"""
    gb = df.groupby("detector_id")
    group_list = [gb.get_group(id) for id in detector_list]
    return [
        np.array(group_df[x_cols]) for group_df in group_list
    ], [
        np.array(group_df[y_cols]) for group_df in group_list
    ]