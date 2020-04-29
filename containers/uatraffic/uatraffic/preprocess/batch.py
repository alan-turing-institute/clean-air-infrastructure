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
    return_df: bool = False,
) -> Tuple:
    """
    Given a dataframe of instances, return a list of models, x_tests and y_tests.

    Args:
        instance_df: Instances queried from the DB.
        secretfile: Path to database secretfile.
        return_df (Optional): If true, return a list of dataframes.

    Returns:
        x_array: List of input test tensors.
        y_array: List of output test tensors.
        df_array (Optional): List of dataframes.
    """
    # load query object
    traffic_query = TrafficQuery(secretfile=secretfile)

    # store tensors and models
    x_dict = {}
    y_dict = {}
    df_dict = {}

    logging.info("Collecting training data from data_config of instances.")
    for data_id in instance_df["data_id"].unique():
        # get first data config matching data id
        row = instance_df.loc[instance_df.data_id == data_id].iloc[0]
        data_config = row["data_config"]
        model_params = row["model_param"]

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
        data_df = normalise_datetime(data_df, wrt=model_params["normaliseby"])

        # add to dicts
        x_dict[data_id] = tf.convert_to_tensor(
            np.array(data_df[data_config["x_cols"]]).astype(np.float64))
        y_dict[data_id] = tf.convert_to_tensor(
            np.array(data_df[data_config["y_cols"]]).astype(np.float64))
        df_dict[data_id] = data_df

    x_array = instance_df["data_id"].map(lambda x: x_dict[x])
    y_array = instance_df["data_id"].map(lambda x: y_dict[x])
    if return_df:
        return x_array, y_array, instance_df["data_id"].map(lambda x: df_dict[x])
    return x_array, y_array
