"""Functions for loading data in batch mode."""
import logging
from typing import Tuple

import pandas as pd
import numpy as np
import tensorflow as tf

from .normalise import normalise_datetime
from ..databases import TrafficQuery

# TODO: this function could be part of an object?
def prepare_batch(
    instance_df: pd.DataFrame,
    secretfile: str,
    normaliseby: str = "clipped_hour",
    x_cols: list = None,
    y_cols: list = None,
) -> Tuple(list, list):
    """
    Given a dataframe of instances, return a list of models, x_tests and y_tests.

    Args:
        instance_df: Instances queried from the DB.
        secretfile: Path to database secretfile.
        normaliseby (optional): Method of time normalisation. Default is 
        x_cols (optional): Names of columns in the input data.
            Default is 'time_norm'.
        y_cols (optional): Names of columns in the target data.
            Default is 'n_vehicles_in_interval'.
    
    Returns:
        x_array: List of input test tensors.
        y_array: List of output test tensors.
    """
    # load query object
    traffic_query = TrafficQuery(secretfile=secretfile)

    # set default x and y columns
    x_cols = ["time_norm"] if not x_cols else x_cols
    y_cols = ["n_vehicles_in_interval"] if not y_cols else y_cols

    # store tensors and models
    x_dict = {}
    y_dict = {}

    logging.info("Collecting training data from data_config of instances.")
    for data_id in instance_df["data_id"].unique():
        # get first data config matching data id
        data_config = instance_df.loc[instance_df.data_id == data_id].iloc[0]["data_config"]

        # get the data for this instance
        data_df = traffic_query.get_scoot_by_dow(
            start_time=data_config["start"],
            end_time=data_config["end"],
            detectors=data_config["detectors"],
            day_of_week=data_config["weekdays"][0],
            output_type="df",
        )
        # normalise
        data_df['measurement_start_utc'] = pd.to_datetime(data_df['measurement_start_utc'])
        data_df = normalise_datetime(data_df, wrt=normaliseby)

        # add to dicts
        x_dict[data_id] = tf.convert_to_tensor(np.array(data_df[x_cols]).astype(np.float64))
        y_dict[data_id] = tf.convert_to_tensor(np.array(data_df[y_cols]).astype(np.float64))

    x_array = instance_df["data_id"].map(lambda x: x_dict[x])
    y_array = instance_df["data_id"].map(lambda x: y_dict[x])
    return x_array, y_array
