import logging
import pandas as pd
import numpy as np


def percent_of_baseline(
    baseline_df, comparison_df, groupby_cols=None, min_condfidence_count=6
):
    """Group both dataframes by detector id and day then """
    try:
        normal_set = set(baseline_df.detector_id)
        comparison_set = set(comparison_df.detector_id)
        assert normal_set == comparison_set
    except AssertionError:
        logging.warning(
            "normal_df and comparison_df have different sensors. Trying to compensate."
        )
    finally:
        detector_set = normal_set.intersection(comparison_set)

    # TODO: remove zeros to avoid skewing the median
    logging.warning("Remember to remove zeros - this still needs to be implemented.")

    # groupby detectorid and hour
    if not groupby_cols:
        groupby_cols = ["detector_id"]
    baseline_gb = baseline_df.groupby("detector_id")
    comparison_gb = comparison_df.groupby("detector_id")

    # keep results in a dataframe
    value_cols = [
        "baseline_n_vehicles_in_interval",
        "comparison_n_vehicles_in_interval",
        "percent_of_baseline",
    ]
    rows_list = []
    baseline_zero_count = 0
    comparison_zero_count = 0

    # iterate over detectors
    for name, group in baseline_gb:
        if name in detector_set:
            flag_dict = dict(
                no_traffic_in_baseline=False,
                no_traffic_in_comparison=False,
                low_confidence=False,  # if we have less than 6 datapoints
            )

            # get the median for each hour
            median_by_hour = group.groupby("hour")["n_vehicles_in_interval"].median()

            # get the dataframe for the recent day for this detector
            day_df = comparison_gb.get_group(name)

            # align series so they have the same hour indices
            i1 = median_by_hour.index
            i2 = day_df.set_index("hour").index
            median_by_hour = median_by_hour[i1.isin(i2)]
            day_df = day_df.loc[i2.isin(i1)]

            # sum all vehicles for this detector
            baseline_n_vehicles_in_interval = median_by_hour.sum()
            comparison_n_vehicles_in_interval = day_df["n_vehicles_in_interval"].sum()

            # count the number of observations and raise flag if there are not many observations
            num_observations = median_by_hour.count()
            flag_dict["low_confidence"] = num_observations < min_condfidence_count

            # handle data when missing values or total vehicles in zero
            if baseline_n_vehicles_in_interval <= 0:
                logging.debug(
                    "Baseline sum is not greater than zero for detector %s.", name
                )
                percent_change = np.nan
                flag_dict["no_traffic_in_baseline"] = True
                baseline_zero_count += 1
            if comparison_n_vehicles_in_interval <= 0:
                logging.debug(
                    "Latest sum is not greater than zero for detector %s.", name
                )
                percent_change = 0
                flag_dict["no_traffic_in_comparison"] = True
                comparison_zero_count += 1
            # calculate percentage difference in normal conditions
            if (
                not flag_dict["no_traffic_in_baseline"]
                and not flag_dict["no_traffic_in_comparison"]
            ):
                percent_change = (
                    100
                    - 100
                    * (
                        baseline_n_vehicles_in_interval
                        - comparison_n_vehicles_in_interval
                    )
                    / baseline_n_vehicles_in_interval
                )

            if len(groupby_cols) > 1:
                index_dict = {
                    groupby_cols[i]: name[i] for i in range(len(groupby_cols))
                }
            else:
                index_dict = {groupby_cols[0]: name}

            row_dict = dict(
                index_dict,
                **flag_dict,
                baseline_n_vehicles_in_interval=baseline_n_vehicles_in_interval,
                comparison_n_vehicles_in_interval=comparison_n_vehicles_in_interval,
                num_observations=num_observations,
                percent_of_baseline=percent_change
            )
            rows_list.append(row_dict)

    logging.info("%s detectors with zero vehicles in normal", baseline_zero_count)
    logging.info("%s detectors with zero vehicles in comparison", comparison_zero_count)
    return pd.DataFrame(rows_list)
