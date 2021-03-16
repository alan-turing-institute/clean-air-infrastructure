"""Functions for calculating the percentage change in traffic."""

from typing import List
import logging
import pandas as pd
import numpy as np


def percent_of_baseline(
    baseline_df: pd.DataFrame,
    comparison_df: pd.DataFrame,
    groupby_cols: List[str] = None,
    min_condfidence_count: int = 6,
) -> pd.DataFrame:
    """Percent change from the baseline for each detector in the comparison dataframe.

    Args:
        baseline_df: Contains observations, possibly for multiple detectors over multiple weeks.
        comparison_df: A single day of observations, possibly for multiple detectors.

    Kwargs:
        groupby_cols: Names of columns in the dataframe to groupby. Default is 'detector_id'.
        min_confidence_count: Minimum number of observations to calculate the percent of baseline
            metric with confidence. Less observations than this value will set the
            `low_confidence` flag to true.

    Returns:
        Percent of baseline metric for each detector with columns for e.g. flags.
    """
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

    # Cast to float
    baseline_df["n_vehicles_in_interval"] = baseline_df[
        "n_vehicles_in_interval"
    ].astype(float)

    # groupby detectorid and hour
    if not groupby_cols:
        groupby_cols = ["detector_id"]
    baseline_gb = baseline_df.groupby("detector_id")
    comparison_gb = comparison_df.groupby("detector_id")

    # keep results in a dataframe
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
            median_index = median_by_hour.index
            day_index = day_df.set_index("hour").index
            median_by_hour = median_by_hour[median_index.isin(day_index)]
            day_df = day_df.loc[day_index.isin(median_index)]

            # sum all vehicles for this detector
            baseline_n_vehicles_in_interval = median_by_hour.sum()
            # pylint: disable=C0103
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
                percent_change = percent_of_baseline_counts(
                    baseline_n_vehicles_in_interval, comparison_n_vehicles_in_interval,
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


def percent_of_baseline_counts(baseline_count: int, comparison_count: int,) -> float:
    """Calculate the percentage change of the comparison count compared to the baseline.

    Args:
        baseline_count: Total count in baseline period.
        comparison_count: Total count in comparison period.

    Returns:
        If comparison_count <= baseline count then returned value will be 0 - 100%.
        Else returned value will be greater than 100%.
    """
    if comparison_count == 0:
        return 0
    if baseline_count == 0:
        return np.nan
    return 100 - 100 * (baseline_count - comparison_count) / baseline_count
