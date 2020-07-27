"""Functionality for the main Spatial Scan loop over a rectangular grid"""
import time
import logging

import pandas as pd
import numpy as np

from .metrics import likelihood_ratio_ebp
from .utils import event_count


def scan(agg_df: pd.DataFrame, grid_resolution: int) -> pd.DataFrame:

    """Main function for looping through the sub-space-time regions (S) of
    global_region represented by data in forecast_data. We search for regions
    with the highest score according to various different metrics. The EBP one is
    given by:
                F(S) := Pr (data | H_1 (S)) / Pr (data | H_0)
    where H_0 and H_1 (S) are defined in the Expectation-Based Scan Statistic
    paper by D. Neill.

    Args:
        agg_df: dataframe consisting of the detectors which lie in
                       global_region, their locations and both their
                       baseline and actual counts for the past W days.
        grid_partition: Split each spatial axis into this many partitions.
    Returns:
        Dataframe summarising each space-time region's F(S) score.
    """

    # Set Initial Timer
    init_time = time.perf_counter()

    # Infer max/min time labels from the input data
    t_min = agg_df.measurement_start_utc.min()
    t_max = agg_df.measurement_end_utc.max()

    # Set up iterators
    x_ticks = range(grid_resolution + 1)
    y_ticks = range(grid_resolution + 1)
    t_ticks = pd.date_range(start=t_min, end=t_max, freq="H")

    # Each search region has spatial extent that covers less than half_max row/columns
    half_max = (
        int(grid_resolution / 2)
        if grid_resolution % 2 == 0
        else int((grid_resolution + 1) / 2)
    )

    # Time direction convention - reverse
    t_ticks = t_ticks[::-1]

    num_regions = 0
    scores_dict = {}
    # Loop over all possible spatial extents of max size grid_resolution/2 in both axes
    for t_min in t_ticks[1:]:  # t_min
        for col_min in x_ticks:  # col_min
            for col_max in range(
                col_min + 1, np.min([col_min + half_max, grid_resolution]) + 1
            ):  # col_max
                for row_min in y_ticks:  # row_min
                    for row_max in range(
                        row_min + 1, np.min([row_min + half_max, grid_resolution]) + 1
                    ):  # row_max

                        # Count up baselines and actual counts here
                        baseline_count, actual_count = event_count(
                            agg_df, col_min, col_max, row_min, row_max, t_min, t_max
                        )

                        # Compute Metric(s)
                        ebp_l_score = likelihood_ratio_ebp(
                            baseline_count, actual_count
                        )  # Normal EBP metric

                        # Append results
                        scores_dict[num_regions] = {
                            "row_min": row_min + 1,
                            "row_max": row_max,
                            "col_min": col_min + 1,
                            "col_max": col_max,
                            "measurement_start_utc": t_min,
                            "measurement_end_utc": t_max,
                            "baseline_count": baseline_count,
                            "actual_count": actual_count,
                            "l_score_ebp": ebp_l_score,
                            # "p_value_EBP": np.nan,
                        }

                        # Count Regions
                        num_regions += 1

        # Log Progress
        logging.info(
            "Search spatial regions with t_min = %s and t_max = %s", t_min, t_max
        )

    scan_time = time.perf_counter()

    logging.info(
        "%d space-time regions searched in %.2f seconds",
        num_regions,
        scan_time - init_time,
    )

    # At this point, we have a dataframe populated with likelihood statistic
    # scores for *each* search region. Sort it so that the highest `l_score_ebp`
    # score is at the top.
    all_scores = pd.DataFrame.from_dict(scores_dict, "index").sort_values(
        "l_score_ebp", ascending=False
    )
    return all_scores


def average_gridcell_scores(
    all_scores: pd.DataFrame, grid_resolution: int
) -> pd.DataFrame:

    """Aggregate scores from the scan to grid level by taking an average of l_score_ebp.
     i.e. For a given grid cell, we find all search regions that contain it, and
     return the average score. Useful for visualisation.
    Args:
        all_scores: Resultgin dataframe from `scan()` method
        grid_resolution: Number of partitions per spatial axis used to create the grid
    Returns:
        grid_level_scores: Average likelihood score per spatial gridcell at each
                           time slice of interest.
    """
    # Set Initial Timer
    init_time = time.perf_counter()

    # TODO Clunky - want ScanScoot object to have Scan parameters built into it
    # i.e. region definitions: borough, grid_res, t_min, t_max, days_in_future (forecast)
    # For now - Infer max/min time labels from the input data
    t_min = all_scores.measurement_start_utc.min()
    t_max = all_scores.measurement_end_utc.max()

    # Set up iterators
    x_ticks = range(grid_resolution + 1)
    y_ticks = range(grid_resolution + 1)
    t_ticks = pd.date_range(start=t_min, end=t_max, freq="H")

    # Time direction convention - reverse
    t_ticks = t_ticks[::-1]

    return_dict = {}
    num_regions = 0
    for t_min in t_ticks[1:]:
        num_spatial_regions = 0

        for row_num in y_ticks[1:]:
            for col_num in x_ticks[1:]:

                gridcell = all_scores[
                    (all_scores["col_min"] <= col_num)
                    & (all_scores["col_max"] >= col_num)
                    & (all_scores["row_min"] <= row_num)
                    & (all_scores["row_max"] >= row_num)
                    & (all_scores["measurement_start_utc"] == t_min)
                ]

                # Calculate mean per gridcell here. Loss of information but
                # easier to interpret
                mean_score = gridcell["l_score_ebp"].mean()
                std = gridcell["l_score_ebp"].std()

                return_dict[num_regions] = {
                    "measurement_start_utc": t_min,
                    "measurement_end_utc": t_max,
                    "row": row_num,
                    "col": col_num,
                    "l_score_ebp_mean": mean_score,
                    "l_score_ebp_std": std,
                }

                num_spatial_regions += 1
                num_regions += 1

    agg_time = time.perf_counter()

    grid_level_scores = pd.DataFrame.from_dict(return_dict, "index")

    logging.info(
        "%d region results aggregated to grid cell level in %.2f seconds",
        num_regions,
        agg_time - init_time,
    )

    return grid_level_scores
