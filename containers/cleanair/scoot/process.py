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

    # get datetime as a float between -1, 1
    df['epoch'] = normalise_daterange(
        df['measurement_start_utc'],
        df['measurement_start_utc'].min(),
        df['measurement_start_utc'].max()
    )
    # normalise all X columns
    # df['epoch_norm'] = normalise(df['epoch'])
    df['lat_norm'] = normalise(df['lat'])
    df['lon_norm'] = normalise(df['lon'])
    return df

def normalise_daterange(dates, start, end, freq="H"):
    date_range = list(pd.date_range(start, end, freq=freq))
    num_dates = len(date_range)
    norm_dates = np.arange(start=-1, stop=1, step=2/(num_dates))
    dates_map = {timestamp: norm for timestamp, norm in zip(date_range, norm_dates)}
    return list(map(dates_map.get, dates))

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
    x_cols=['epoch', 'lon_norm', 'lat_norm'],
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