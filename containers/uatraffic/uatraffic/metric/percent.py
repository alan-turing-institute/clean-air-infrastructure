
import logging
import pandas as pd

def percent_of_baseline(baseline_df, latest_df, groupby_cols=None, ignore_missing=False):
    """Group both dataframes by detector id and day then """
    try:
        normal_set = set(baseline_df.detector_id)
        latest_set = set(latest_df.detector_id)
        assert normal_set == latest_set
    except AssertionError:
        logging.warning("normal_df and latest_df have different sensors. Trying to compensate.")
    finally:
        detector_set = normal_set.intersection(latest_set)

    # TODO: remove zeros to avoid skewing the median
    logging.warning("Remember to remove zeros - this still needs to be implemented.")

    # groupby detectorid and hour
    if not groupby_cols:
        groupby_cols = ["detector_id"]
    baseline_gb = baseline_df.groupby("detector_id")
    latest_gb = latest_df.groupby("detector_id")

    # keep results in a dataframe
    value_cols = ["baseline_n_vehicles_in_interval", "latest_n_vehicles_in_interval", "percent_of_baseline"]
    rows_list = []
    normal_zero_count = []
    latest_zero_count = []
    different_count = []

    # iterate over detectors
    for name, group in baseline_gb:
        if name in detector_set:
            # get the median for each hour
            median_by_hour = group.groupby("hour")["n_vehicles_in_interval"].median()

            # get the dataframe for the recent day for this detector
            day_df = latest_gb.get_group(name)

            # align series so they have the same hour indices
            i1 = median_by_hour.index
            i2 = day_df.set_index("hour").index
            median_by_hour = median_by_hour[i1.isin(i2)]
            day_df = day_df.loc[i2.isin(i1)]

            # sum all vehicles in the normal day for this detector
            baseline_n_vehicles_in_interval = median_by_hour.sum()
            try:
                assert baseline_n_vehicles_in_interval > 0
            except AssertionError:
                logging.debug("Normal sum is not greater than zero for detector %s. Setting normal sum to 1.", name)
                normal_zero_count.append(name)
                baseline_n_vehicles_in_interval = 1
            
            # sum all vehicles in the latest day for this detector
            # ToDo: is this oK to set to 1?
            latest_n_vehicles_in_interval = day_df["n_vehicles_in_interval"].sum()
            try:
                assert latest_n_vehicles_in_interval > 0
            except AssertionError:
                logging.debug("Latest sum is not greater than zero for detector %s. Setting latest sum to 1.", name)
                latest_zero_count.append(name)
                latest_n_vehicles_in_interval = 1
                
            percent_change = 100 - 100 * (baseline_n_vehicles_in_interval - latest_n_vehicles_in_interval) / baseline_n_vehicles_in_interval

            if len(groupby_cols) > 1:
                index_dict = {groupby_cols[i]: name[i] for i in range(len(groupby_cols))}
            else:
                index_dict = {groupby_cols[0]: name}

            row_dict = dict(
                index_dict,
                baseline_n_vehicles_in_interval=baseline_n_vehicles_in_interval,
                latest_n_vehicles_in_interval=latest_n_vehicles_in_interval,
                percent_of_baseline=percent_change
            )
            rows_list.append(row_dict)

    logging.info("%s detectors with zero vehicles in normal", len(normal_zero_count))
    logging.info("%s detectors with zero vehicles in latest", len(latest_zero_count))
    logging.info("%s detectors with different number of observations.", len(different_count))
    return pd.DataFrame(rows_list)
