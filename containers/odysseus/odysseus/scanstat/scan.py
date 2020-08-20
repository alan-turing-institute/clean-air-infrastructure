"""Functionality for the main Spatial Scan loop over a rectangular grid"""
import time
import logging
import datetime

import pandas as pd
import numpy as np

from .metrics import ebp, ebp_asym, kulldorf
from .utils import event_count


def scan(
    agg_df: pd.DataFrame,
    grid_resolution: int,
    forecast_start: datetime,
    forecast_end: datetime,
) -> pd.DataFrame:

    """Main function for looping through the sub-space-time regions (S) of
    global_region represented by data in agg_df. We search for regions
    with the highest score according to various different metrics. The EBP one is
    given by:
                F(S) := Pr (data | H_1 (S)) / Pr (data | H_0)
    where H_0 and H_1 (S) are defined in the Expectation-Based Scan Statistic
    paper by D. Neill. Results are by default, sorted in descending order w.r.t
    this metric.

    Args:
        agg_df: dataframe consisting of grid-level, time-indexed counts and estimates.
        grid_partition: Split each spatial axis into this many partitions.
        forecast_start: forecast start time
        forecast_end: forecast end time
    Returns:
        Dataframe summarising each space-time region's scan statistics.
    """

    # Set Initial Timer
    init_time = time.perf_counter()

    # Set up iterators
    x_ticks = range(grid_resolution + 1)
    y_ticks = range(grid_resolution + 1)
    t_min, t_max = forecast_start, forecast_end
    t_ticks = pd.date_range(start=t_min, end=t_max, freq="H")

    # Each search region has spatial extent that covers less than half_max row/columns
    half_max = (
        int(grid_resolution / 2)
        if grid_resolution % 2 == 0
        else int((grid_resolution + 1) / 2)
    )

    # Kulldorf metric requires total baselines and total actual counts
    baseline_total = agg_df["baseline"].sum() / 1e6
    baseline_total_upper = agg_df["baseline_upper"].sum() / 1e6
    baseline_total_lower = agg_df["baseline_lower"].sum() / 1e6
    actual_total = agg_df["actual"].sum() / 1e6

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

                        # Count up baselines and actual counts within region here
                        counts = event_count(
                            agg_df, col_min, col_max, row_min, row_max, t_min, t_max
                        )
                        (
                            baseline,
                            baseline_upper,
                            baseline_lower,
                            actual,
                        ) = counts.values()

                        # Compute Metric(s)
                        ebp_score = ebp(baseline, actual)
                        ebp_score_upper = ebp(baseline_lower, actual)
                        ebp_score_lower = ebp(baseline_upper, actual)

                        kulldorf_score = kulldorf(
                            baseline, baseline_total, actual, actual_total
                        )
                        kulldorf_score_upper = kulldorf(
                            baseline_lower, baseline_total_lower, actual, actual_total
                        )
                        kulldorf_score_lower = kulldorf(
                            baseline_upper, baseline_total_upper, actual, actual_total
                        )

                        ebp_asym_score = ebp_asym(baseline, actual)
                        ebp_asym_upper = ebp_asym(baseline_lower, actual)
                        ebp_asym_lower = ebp_asym(baseline_upper, actual)

                        # Append results
                        scores_dict[num_regions] = {
                            "row_min": row_min + 1,
                            "row_max": row_max,
                            "col_min": col_min + 1,
                            "col_max": col_max,
                            "measurement_start_utc": t_min,
                            "measurement_end_utc": t_max,
                            "baseline": baseline,
                            "baseline_upper": baseline_upper,
                            "baseline_lower": baseline_lower,
                            "actual": actual,
                            "ebp_lower": ebp_score_lower,
                            "ebp": ebp_score,
                            "ebp_upper": ebp_score_upper,
                            "kulldorf_lower": kulldorf_score_lower,
                            "kulldorf": kulldorf_score,
                            "kulldorf_upper": kulldorf_score_upper,
                            "ebp_asym_lower": ebp_asym_lower,
                            "ebp_asym": ebp_asym_score,
                            "ebp_asym_upper": ebp_asym_upper,
                        }

                        # Count Regions
                        num_regions += 1

        # Log Progress
        logging.info(
            "Searching spatial regions with t_min = %s and t_max = %s", t_min, t_max
        )

    scan_time = time.perf_counter()

    logging.info(
        "%d space-time regions searched in %.2f seconds",
        num_regions,
        scan_time - init_time,
    )

    # At this point, we have a dataframe populated with likelihood statistic
    # scores for *each* search region. Sort it so that the highest `ebp`
    # score is at the top.
    all_scores = pd.DataFrame.from_dict(scores_dict, "index").sort_values(
        "ebp", ascending=False
    )
    return all_scores


def average_gridcell_scores(
    all_scores: pd.DataFrame,
    grid_resolution: int,
    forecast_start: datetime,
    forecast_end: datetime,
) -> pd.DataFrame:

    """Aggregate scores from the scan to grid level by taking an average of the metrics.
     i.e. For a given grid cell, we find all search regions that contain it, and
     return the average score. Useful for visualisation.
    Args:
        all_scores: Resulting dataframe from `scan()` method
        grid_resolution: Number of partitions per spatial axis used to create the grid
    Returns:
        grid_level_scores: Average likelihood score per spatial gridcell at each
                           time slice of interest.
    """
    # Set Initial Timer
    init_time = time.perf_counter()

    # Set up iterators
    x_ticks = range(grid_resolution + 1)
    y_ticks = range(grid_resolution + 1)
    t_min, t_max = forecast_start, forecast_end
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
                mean_scores = gridcell[
                    [
                        "ebp_lower",
                        "ebp",
                        "ebp_upper",
                        "kulldorf_lower",
                        "kulldorf",
                        "kulldorf_upper",
                        "ebp_asym_lower",
                        "ebp_asym",
                        "ebp_asym_upper",
                    ]
                ].mean()

                return_dict[num_regions] = {
                    "measurement_start_utc": t_min,
                    "measurement_end_utc": t_max,
                    "row": row_num,
                    "col": col_num,
                    "ebp_lower": mean_scores["ebp_lower"],
                    "ebp": mean_scores["ebp"],
                    "ebp_upper": mean_scores["ebp_upper"],
                    "kulldorf_lower": mean_scores["kulldorf_lower"],
                    "kulldorf": mean_scores["kulldorf"],
                    "kulldorf_upper": mean_scores["kulldorf_upper"],
                    "ebp_asym_lower": mean_scores["ebp_asym_lower"],
                    "ebp_asym": mean_scores["ebp_asym"],
                    "ebp_asym_upper": mean_scores["ebp_asym_upper"],
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
