"""
Methods for detecting and removing anomalies.
"""

import logging


def remove_outliers(scoot_df, k=3, col="n_vehicles_in_interval"):
    r"""Remove outliers $x$ where $|x - \mu| > k \sigma$ for each detector."""
    to_remove = get_index_of_outliers(scoot_df, k=k, col=col)
    logging.info("Removed %s anomalous readings out of %s total readings", len(to_remove), len(scoot_df))
    return scoot_df.loc[~scoot_df.index.isin(set(to_remove))]


def get_index_of_outliers(scoot_df, k=3, col="n_vehicles_in_interval"):
    """Returns a list of indices that are outliers."""
    # remove outliers
    to_remove = []  # list of indices to remove

    # groupby detector id
    for _, group in scoot_df.groupby("detector_id"):
        remove_in_group = group.index[
            abs(group[col] - group[col].mean()) > k * group[col].std()
        ].tolist()
        to_remove.extend(remove_in_group)
    return to_remove
