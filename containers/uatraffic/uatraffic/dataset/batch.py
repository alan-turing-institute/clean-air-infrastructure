"""Functions for loading data in batch mode."""
import logging
from typing import Tuple
import pandas as pd
from .traffic_dataset import TrafficDataset

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

        # get the dataset for this instance
        # TODO: pass model_params to TrafficDataset for normalisation
        dataset = TrafficDataset(data_config, secretfile)
        df_dict[data_id] = dataset.dataframe
        x_dict[data_id] = dataset.features
        y_dict[data_id] = dataset.target

        # TODO: move this to Dataset class
        # add to dicts
        # if getattr(model_params, "median"):
        #     gb = data_df.groupby(data_config["x_cols"])
        #     median = gb[data_config["y_cols"]].median
        #     x_train = np.array(gb.index)
        #     y_train = np.array(median)
        #     # TODO remove assert
        #     assert x_train.shape[0] == 24
        # else:
        #     x_train = np.array(data_df[data_config["x_cols"]]).astype(np.float64)
        #     y_train = np.array(data_df[data_config["y_cols"]]).astype(np.float64)

    x_array = instance_df["data_id"].map(lambda x: x_dict[x])
    y_array = instance_df["data_id"].map(lambda x: y_dict[x])
    if return_df:
        return x_array, y_array, instance_df["data_id"].map(lambda x: df_dict[x])
    return x_array, y_array
