"""Functionality to remove anomalies, and deal with missing data before scanning."""

import logging

import numpy as np
import pandas as pd

from geoalchemy2.shape import to_shape


def preprocessor(
    scoot_df: pd.DataFrame,
    max_anom_per_day: int = 1,
    n_sigma: int = 3,
    repeats: int = 1,
    rolling_hours: int = 24,
    global_threshold: bool = False,
    percentage_missing: float = 20,
) -> pd.DataFrame:

    """Takes a SCOOT dataframe, performs anomaly removal, fills missing readings, and then
    interpolates missing values if sufficiently few of them.

    Args:
        scoot_df: dataframe of SCOOT data
        n_sigma: number of standard deviations from the median to set anomaly threshold
        repeats: number of iterations for anomaly removal
        rolling_hours: number of previous hours used to calculate rolling median
        global_threshold: if True, global median used for threshold instead of rolling median
        percentage_missing: percentage of missing values, above which, drop detector

    Returns:
        Dataframe of interpolated values with detectors dropped for too many missing
        values or anomalies.
    """
    columns = [
        "detector_id",
        "lon",
        "lat",
        "location",
        "measurement_start_utc",
        "measurement_end_utc",
        "n_vehicles_in_interval",
    ]

    if not set(columns) <= set(scoot_df.columns):
        raise KeyError("Input dataframe has missing columns")
    if percentage_missing < 0:
        raise ValueError("percentage_missing must be non-negative")
    if max_anom_per_day < 0:
        raise ValueError("max_anom_per_day must be a non-negative integer")
    if n_sigma < 0:
        raise ValueError("n_sigma must be non-negative integer")
    if repeats < 0:
        raise ValueError("repeats must be non-negative integer")
    if rolling_hours < 0 and not global_threshold:
        raise ValueError("rolling_hours must be non-negative")

    # TODO - Remove this once scoot_fishnet_query gives one column each
    # First remove duplicate columns
    scoot_df = scoot_df.loc[:, ~scoot_df.columns.duplicated()].copy()

    scoot_df.sort_values(['detector_id', 'measurement_end_utc'], inplace=True)

    # Convert location wkb to wkt, so can use groupby later on
    scoot_df["location"] = scoot_df["location"].apply(to_shape).apply(lambda x: x.wkt)
    # Drop geom column as not needed for scan
    scoot_df = scoot_df.drop('geom', axis=1)

    # Convert dates to useful format
    scoot_df["measurement_start_utc"] = pd.to_datetime(
        scoot_df["measurement_start_utc"]
    )
    scoot_df["measurement_end_utc"] = pd.to_datetime(scoot_df["measurement_end_utc"])

    # Get time range of input dataframe
    start_date = scoot_df["measurement_start_utc"].min()
    end_date = scoot_df["measurement_end_utc"].max()
    num_days = (end_date - start_date).days

    # Max allowable amount of anomalies without detector disposal
    max_anom = max_anom_per_day * num_days

    # Create array of times for which we want data
    end_times = pd.date_range(
        start=start_date + np.timedelta64(1, "h"), end=end_date, freq="H",
    )

    # Create Multi-index dataframe
    scoot_df = scoot_df.set_index(["detector_id", "measurement_end_utc"])

    # Drop duplicates - some detectors are mapped to two grid cells
    # If this is true, we keep the first.
    scoot_df = scoot_df.loc[~scoot_df.index.duplicated(keep='first')]

    # Calculate original num of detectors inputted by user
    orig_set = set(scoot_df.index.get_level_values("detector_id"))
    orig_length = len(orig_set)

    if global_threshold:
        logging.info(
            "Using the global median over %d days to remove outliers", num_days
        )
    else:
        logging.info(
            "Using the %d-day rolling median to remove outliers", rolling_hours
        )
    logging.info(
        "Using %d iterations to remove points outside of %d sigma from the median",
        repeats,
        n_sigma,
    )

    # Anomaly Removal - Drop detectors with too many according to `max_anom_per_day`
    scoot_df = remove_anomalies(
        scoot_df, max_anom, n_sigma, repeats, rolling_hours, global_threshold
    )

    # Missing Data Removal
    scoot_df = drop_sparse_detectors(scoot_df, percentage_missing, end_times)

    # Return drop information to user
    curr_set = set(scoot_df.index.get_level_values("detector_id"))
    curr_length = len(curr_set)
    logging.info(
        "%d detectors dropped: %s",
        orig_length - curr_length,
        orig_set.difference(curr_set),
    )

    # Interpolate missing counts and fill missing lon, lats, locations etc.
    proc_df = fill_missing_values(scoot_df, method="linear")

    logging.info("Data processing complete.")
    return proc_df


def remove_anomalies(
    scoot_df: pd.DataFrame,
    max_anom: int,
    n_sigma: int,
    repeats: int,
    rolling_hours: int,
    global_threshold: bool,
) -> pd.DataFrame:

    """Remove anomalies from the input dataframe.
    Args:
        scoot_df: DataFrame of Raw Scoot Data
        max_anom: Maximum number of allowed anomalies in a detector time-series.
                  Otherwise, removed.
        n_sigma: Number of std devs away from the median to create the anomaly threshold
        repeats: Number of times to repeat the anomaly removal process
        rolling_hours: Number of hours used in the the rolling median calculation
        global_threshold: Choose to use rolling median with rolling_hours window
                          or a fixed global median.
    Returns:
        scoot_df: DataFrame free from anomalies
    """

    scoot_df = scoot_df.sort_values(["detector_id", "measurement_end_utc"])

    for rep in range(0, repeats):

        scoot_df["rolling_threshold"] = (
            scoot_df.groupby(level="detector_id")["n_vehicles_in_interval"]
            .rolling(window=rolling_hours)
            .median()
            .values
            + n_sigma
            * scoot_df.groupby(level="detector_id")["n_vehicles_in_interval"]
            .rolling(window=rolling_hours)
            .std()
            .values
        )

        scoot_df = scoot_df.join(
            scoot_df.median(level="detector_id")["n_vehicles_in_interval"]
            + n_sigma * (scoot_df.std(level="detector_id")["n_vehicles_in_interval"]),
            on=["detector_id"],
            rsuffix="anom",
        )

        scoot_df["global_threshold"] = scoot_df["n_vehicles_in_intervalanom"]
        scoot_df = scoot_df.drop(["n_vehicles_in_intervalanom"], axis=1)

        scoot_df["rolling_threshold"] = scoot_df["rolling_threshold"].fillna(
            scoot_df["global_threshold"]
        )

        if global_threshold:
            scoot_df["rolling_threshold"] = scoot_df["global_threshold"]

        scoot_df.loc[
            scoot_df["n_vehicles_in_interval"] > scoot_df["rolling_threshold"],
            ["n_vehicles_in_interval"],
        ] = float("NaN")

        logging.info(
            "Calculating threshold(s): Iteration %d of %d\r", rep + 1, repeats,
        )

    # Calculate number of anomalies per detector
    scoot_df = scoot_df.join(
        scoot_df.isna().astype(int).sum(level="detector_id")["n_vehicles_in_interval"],
        on=["detector_id"],
        rsuffix="NaN",
    )
    scoot_df.rename({"n_vehicles_in_intervalNaN": "num_anom"}, axis=1, inplace=True)

    # Drop detectors with too many anomalies
    logging.info("Dropping detectors with more than %d anomalies", max_anom)
    dropped_df = scoot_df.drop(scoot_df[scoot_df["num_anom"] > max_anom].index)

    return dropped_df


def drop_sparse_detectors(
    scoot_df: pd.DataFrame, percentage_missing: int, end_times: np.ndarray
) -> pd.DataFrame:

    """Remove detectors from the dataframe with too many missing values over
    the time range of the input dataframe.
    Args:
        scoot_df: Dataframe of scoot data (preferably free from anomalies)
        percentage_missing: A detector above percentage_missing of missing data
                             will be removed from the dataframe
        end_times: Array of measurement times for which we want measurements for.
    Returns:
        scoot_df: DataFrame free from detectors with sufficiently high amounts of
                  missing data.
    """

    logging.info("Filling in missing dates and times")
    remaining_detectors = scoot_df.index.get_level_values("detector_id").unique()
    mux = pd.MultiIndex.from_product(
        [remaining_detectors, end_times], names=("detector_id", "measurement_end_utc")
    )
    scoot_df = scoot_df.reindex(mux)

    # Find detectors with too much missing data
    detectors_to_drop = []
    for det in remaining_detectors:
        if (
            scoot_df.loc[det]["n_vehicles_in_interval"].isna().sum()
            > len(end_times) * 0.01 * percentage_missing
        ):
            detectors_to_drop.append(det)

    logging.info(
        "Dropping detectors with sufficiently high amounts of missing data (> %d%%)",
        percentage_missing,
    )

    # If there are detectors to be dropped, remove them.
    if detectors_to_drop:
        scoot_df.drop(detectors_to_drop, level="detector_id", inplace=True)

    return scoot_df


def fill_missing_values(scoot_df: pd.DataFrame, method: str = "linear") -> pd.DataFrame:

    """Fills the missing values of the remaining detectors with sufficiently low
    amounts of missing data. Vehicle counts are interpolated, other columns are
    padded out.

    Args:
        scoot_df: DataFrame of SCOOT data with added rows representing missing readings
        method: Use this method for interpolation of vehicle counts
    Returns:
        scoot_df: Full SCOOT dataframe with interpolated/filled values.
    """

    # Linearly interpolate missing vehicle counts whilst still using multi_index
    # Fills backwards and forwards
    logging.info(
        "Using %s method to interpolate between missing vehicle counts of remaining detectors",
        method,
    )
    scoot_df["n_vehicles_in_interval"] = scoot_df["n_vehicles_in_interval"].interpolate(
        method=method, limit_direction="both", axis=0
    )

    # Create the remaining columns/fill missing row values
    logging.info("Padding the remaining columns with existing values")
    scoot_df["measurement_start_utc"] = scoot_df.index.get_level_values(
        "measurement_end_utc"
    ) - np.timedelta64(1, "h")
    scoot_df = scoot_df.reset_index()
    scoot_df.sort_values(["detector_id", "measurement_end_utc"], inplace=True)

    # Fill missing lon, lat, rolling, global columns with existing values
    scoot_df = scoot_df.groupby("detector_id").apply(lambda x: x.ffill().bfill())

    # Re-Order Columns
    scoot_df = scoot_df[
        [
            "detector_id",
            "lon",
            "lat",
            "location",
            "row",
            "col",
            "measurement_start_utc",
            "measurement_end_utc",
            "n_vehicles_in_interval",
            "rolling_threshold",
            "global_threshold",
        ]
    ]
    return scoot_df
