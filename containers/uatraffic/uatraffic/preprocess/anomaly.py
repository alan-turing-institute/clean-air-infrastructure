"""
Methods for detecting and removing anomalies.
"""

import logging
from typing import List
import pandas as pd


def remove_outliers(
    scoot_df: pd.DataFrame,
    sigmas: int = 3,
    col: str = "n_vehicles_in_interval",
) -> pd.DataFrame:
    r"""Remove outliers $x$ where $|x - \mu| > k \sigma$ for each detector where $k$ is `sigmas`.

    Args:
        scoot_df: Scoot data.
        sigmas: Number of standard deviations from the mean.
        col: Name of the column to look for anomalies.

    Returns:
        Data with no anomalies.
    """
    to_remove = get_index_of_outliers(scoot_df, sigmas=sigmas, col=col)
    logging.info(
        "Removed %s anomalous readings out of %s total readings",
        len(to_remove),
        len(scoot_df),
    )
    return scoot_df.loc[~scoot_df.index.isin(set(to_remove))]


def get_index_of_outliers(
    scoot_df: pd.DataFrame,
    sigmas: int = 3,
    col: str = "n_vehicles_in_interval",
) -> List:
    """Returns a list of indices that are outliers."""
    # remove outliers
    to_remove = []  # list of indices to remove

    # groupby detector id
    for _, group in scoot_df.groupby("detector_id"):
        remove_in_group = group.index[
            (abs(group[col] - group[col].mean()) > sigmas * group[col].std()) |
            (group[col] < 0)
        ].tolist()
        to_remove.extend(remove_in_group)
    return to_remove
