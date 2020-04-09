
import logging
import pandas as pd

def percent_of_baseline(baseline_gb, latest_gb, groupby_cols=["detector_id"], debug=False, ignore_missing=False):
    """Group both dataframes by detector id and day then """
    try:
        normal_set = set(baseline_gb.keys())
        latest_set = set(latest_gb.keys())
        assert normal_set == latest_set
    except AssertionError:
        logging.warning("normal_df and latest_df have different sensors. Trying to compensate.")
    finally:
        detector_set = normal_set.intersection(latest_set)
    
    # keep results in a dataframe
    value_cols = ["normal_sum", "latest_sum", "percent_of_normal"]
    rows_list = []
    normal_zero_count = []
    latest_zero_count = []
    different_count = []
    
    for name, group in baseline_gb:
        if name in detector_set:
            try:
                assert list(group["hour"].sort_values()) == list(latest_gb.get_group(name)["hour"].sort_values())
            except AssertionError:
                if ignore_missing:
                    different_count.append(name)
                else:
                    raise ValueError("Both dataframes should have the same entries for each hour. See align_dfs_by_hour().")

            # sum all vehicles in the normal day for this detector
            normal_sum = group["n_vehicles_in_interval"].sum()
            try:
                assert normal_sum > 0
            except AssertionError:
                logging.debug("Normal sum is not greater than zero for detector %s. Setting normal sum to 1.", name)
                normal_zero_count.append(name)
                normal_sum = 1
            
            # sum all vehicles in the latest day for this detector
            # ToDo: is this oK to set to 1?
            latest_sum = latest_gb.get_group(name)["n_vehicles_in_interval"].sum()
            try:
                assert latest_sum > 0
            except AssertionError:
                logging.debug("Latest sum is not greater than zero for detector %s. Setting latest sum to 1.", name)
                latest_zero_count.append(name)
                latest_sum = 1
                
            percent_change = 100 - 100 * (normal_sum - latest_sum) / normal_sum

            if len(groupby_cols) > 1:
                index_dict = {groupby_cols[i]: name[i] for i in range(len(groupby_cols))}
            else:
                index_dict = {groupby_cols[0]: name}

            row_dict = dict(
                index_dict,
                normal_sum=normal_sum,
                latest_sum=latest_sum,
                percent_of_normal=percent_change
            )
            rows_list.append(row_dict)

    logging.info("%s detectors with zero vehicles in normal", len(normal_zero_count))
    logging.info("%s detectors with zero vehicles in latest", len(latest_zero_count))
    logging.info("%s detectors with different number of observations.", len(different_count))
    return pd.DataFrame(rows_list)
