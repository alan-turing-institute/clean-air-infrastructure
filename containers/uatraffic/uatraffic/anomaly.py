import logging

def remove_outliers(df, k=3, col="n_vehicles_in_interval"):
    """Remove outliers $x$ where $|x - \mu| > k \sigma$ for each detector."""
    to_remove = get_index_of_outliers(df, k=3, col=col)
    logging.info("Removed %s anomalous readings.", len(to_remove))
    logging.info("Total %s readings.", len(df))
    return df.loc[~df.index.isin(set(to_remove))]


def get_index_of_outliers(gb, k=3, col="n_vehicles_in_interval"):
    """Returns a list of indices that are outliers."""
    # remove outliers
    to_remove = []  # list of indices to remove

    for detector_id, group in gb:
        remove_in_group = group.index[
            abs(group[col] - group[col].mean()) > k * group[col].std()
        ].tolist()
        to_remove.extend(remove_in_group)
    return to_remove

def align_dfs_by_hour(df1, df2):
    """
    If df1 is missing a row for a given detector at a given hour, then remove that row from df2.
    Repeat for df2.
    
    Parameters
    ___
    
    df1 : pd.DataFrame
    
    df2 : pd.DataFrame
    
    Returns
    ___
    
    df1 : pd.DataFrame
        Same number of rows as df2.
        
    df2 : pd.DataFrame
    """
    # ToDo: do a join
    keys = ["detector_id", "hour"]
    i1 = df1.set_index(keys).index
    i2 = df2.set_index(keys).index

    df1 = df1.loc[i1.isin(i2)]
    df2 = df2.loc[i2.isin(i1)]
