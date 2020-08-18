"""Contains all utility functionality required for Spatial Scan statistics."""

import datetime
import pandas as pd


def aggregate_readings_to_grid(forecast_df: pd.DataFrame) -> pd.DataFrame:

    """Aggregates data from each detector in forecast_df to grid-cell level
    as prescribed by detector_df.
    Args:
        forecast_df: Forecasted SCOOT data from time series analysis
    Returns:
        agg_df: dataframe of SCOOT data aggregated to the spatial grid at hourly
                time steps. Actual counts and baseline estimates are aggregated as
                separate columns in the returned dataframe.
    """

    assert set(
        [
            "detector_id",
            "measurement_start_utc",
            "measurement_end_utc",
            "lon",
            "lat",
            "location",
            "actual",
            "row",
            "col",
            "baseline",
            "baseline_upper",
            "baseline_lower",
            "standard_deviation",
        ]
    ).issubset(set(forecast_df.columns))

    # These columns make no sense when aggregating to grid level, so drop
    agg_df = forecast_df.drop(
        ["detector_id", "lon", "lat", "location", "standard_deviation"], axis=1
    )

    # Sum counts and baselines at grid cell level
    agg_df = agg_df.groupby(
        ["row", "col", "measurement_start_utc", "measurement_end_utc"]
    ).sum()

    # Convert back to normal dataframe
    agg_df = agg_df.reset_index()

    return agg_df


def event_count(
    agg_df: pd.DataFrame,
    col_min: int,
    col_max: int,
    row_min: int,
    row_max: int,
    t_min: datetime,
    t_max: datetime,
) -> dict:

    """Aggregate the vehicle counts that fall within the region specified by
    the last 6 arguments (row/colums/time identifiers). Scaled by 1e6 for metric
    calculation.

    Args:
        agg_df: SCOOT data for actual counts and baselines aggregated to grid-cell
                level
        col_min: left boundary column number of search region (inclusive)
        col_max: right boundary column number of search region (inclusive)
        row_min: bottom boundary row_number of search region (inclusive)
        row_max: top boundary row_number of search region (inclusive)
        t_min: earliest time defining the space-time region (inclusive)
        t_max: latest_time defining the space-time region (inclusive)
    Returns:
        dictionary with keys:
            baseline: sum of detector baseline estimates in search region
            baseline_upper: sum of detector upper-estimate baseline estimates in search region
            baseline_lower: sum of detector lower-estimate baseline estimates in search region
            actual: sum of actual detector counts in search region
    Notes:
        t_max is fixed currently. The scan statistic is calculated for all space-time
        regions such that t_max is the most recent day. The search is then conducted
        over the space time regions that begin before t_max.
    """

    # Check for columns existence.
    assert set(
        [
            "row",
            "col",
            "measurement_start_utc",
            "measurement_end_utc",
            "actual",
            "baseline",
            "baseline_upper",
            "baseline_lower",
        ]
    ) <= set(agg_df.columns)

    # Find all space-time regions that are a subset of the region described
    # in the arguments of this function.
    search_region_mask = (
        (agg_df["col"].between(col_min, col_max))
        & (agg_df["row"].between(row_min, row_max))
        & (agg_df["measurement_start_utc"] >= t_min)
        & (agg_df["measurement_end_utc"] <= t_max)
    )

    search_region_data = agg_df.loc[search_region_mask]

    if search_region_data.empty:
        return {"baseline": 0, "baseline_upper": 0, "baseline_lower": 0, "actual": 0}
    return {
        "baseline": search_region_data["baseline"].sum() / 1e6,
        "baseline_upper": search_region_data["baseline_upper"].sum() / 1e6,
        "baseline_lower": search_region_data["baseline_lower"].sum() / 1e6,
        "actual": search_region_data["actual"].sum() / 1e6,
    }
