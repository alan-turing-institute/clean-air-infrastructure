"""Functions for loading data in batch mode."""
import logging
from typing import List
import pandas as pd
from .scoot_dataset import ScootDataset


def prepare_batch(instance_df: pd.DataFrame, secretfile: str,) -> List[ScootDataset]:
    """
    Given a dataframe of instances, return a list of models, x_tests and y_tests.

    Args:
        instance_df: Instances queried from the DB.
        secretfile: Path to database secretfile.

    Returns:
        List of Dataset objects.
    """
    # store datasets in dictionary
    datasets = dict()

    logging.info("Collecting training data from data_config of instances.")
    for data_id in instance_df["data_id"].unique():
        # get first data config matching data id
        row = instance_df.loc[instance_df.data_id == data_id].iloc[0]
        data_config = row["data_config"]
        preprocessing = row["preprocessing"]

        # get the dataset for this instance
        datasets[data_id] = ScootDataset(data_config, preprocessing, secretfile)

    return instance_df["data_id"].map(lambda x: datasets[x])
