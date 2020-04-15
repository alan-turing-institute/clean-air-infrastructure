import logging


def remove_outliers(df, k=3, col="n_vehicles_in_interval"):
    """Remove outliers $x$ where $|x - \mu| > k \sigma$ for each detector."""
    to_remove = get_index_of_outliers(df, k=k, col=col)
    logging.info("Removed %s anomalous readings.", len(to_remove))
    logging.info("Total %s readings.", len(df))
    return df.loc[~df.index.isin(set(to_remove))]


def get_index_of_outliers(df, k=3, col="n_vehicles_in_interval"):
    """Returns a list of indices that are outliers."""
    # remove outliers
    to_remove = []  # list of indices to remove

    # groupby detector id
    gb = df.groupby("detector_id")

    for detector_id, group in gb:
        remove_in_group = group.index[
            abs(group[col] - group[col].mean()) > k * group[col].std()
        ].tolist()
        to_remove.extend(remove_in_group)
    return to_remove