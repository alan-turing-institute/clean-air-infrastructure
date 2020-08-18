"""Functionality to remove anomalies, and deal with missing data before scanning."""

import logging
from typing import Tuple

import numpy as np
import pandas as pd

from geoalchemy2.shape import to_shape
from astropy.timeseries import LombScargle


def preprocessor(
    scoot_df: pd.DataFrame,
    readings_type="",
    percentage_missing: float = 20,
    max_anom_per_day: int = 1,
    n_sigma: int = 3,
    repeats: int = 1,
    global_threshold: bool = False,
    rolling_hours: int = 24,
    consecutive_missing_threshold: int = 3,
    drop_aperiodic: bool = False,
    fap_percentile_threshold: float = 0.95,
) -> pd.DataFrame:

    """Takes a SCOOT dataframe, performs anomaly removal, fills missing readings, and then
    interpolates missing values if sufficiently few of them.

    Args:
        scoot_df: dataframe of SCOOT data
        percentage_missing: percentage of missing values, above which, drop detector
        n_sigma: number of standard deviations from the median to set anomaly threshold
        repeats: number of iterations for anomaly removal
        global_threshold: if True, global median used for threshold instead of rolling median
        rolling_hours: number of previous hours used to calculate rolling median
        consecutive_missing_threshold:
        drop_aperiodic: User choice to decide whether to run periodicity checks
        fap_threshold: detectors with false-alarm-probability above this value
                       will be dropped from further analysis

    Returns:
        Dataframe of interpolated values with detectors dropped for too many missing
        values or anomalies.
    """
    columns = [
        "detector_id",
        "point_id",
        "geom",
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

    if readings_type:
        logging.info("Preprocessing %s data", readings_type.upper())

    # Sort values for nice multi-indexing printing
    scoot_df.sort_values(["detector_id", "measurement_end_utc"], inplace=True)

    # Convert location wkb to wkt, so can use groupby later on
    scoot_df["location"] = scoot_df["location"].apply(to_shape).apply(lambda x: x.wkt)

    # Drop geom and point_id column as not needed for scan - will merge on at the end
    scoot_df = scoot_df.drop(["geom", "point_id"], axis=1)

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
    scoot_df = scoot_df.loc[~scoot_df.index.duplicated(keep="first")]

    # Calculate original num of detectors inputted by user
    orig_length = len(set(scoot_df.index.get_level_values("detector_id")))

    if global_threshold:
        logging.info(
            "Using the global median over %d days to remove outliers", num_days
        )
    else:
        logging.info(
            "Using the %d-hour rolling median to remove outliers", rolling_hours
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
    scoot_df = drop_sparse_detectors(
        scoot_df, end_times, percentage_missing, consecutive_missing_threshold
    )

    # Return drop information to user
    curr_length = len(set(scoot_df.index.get_level_values("detector_id")))
    logging.info(
        "%d detectors dropped", orig_length - curr_length,
    )

    # Linearly interpolate missing vehicle counts whilst still using multi_index
    # Fills backwards and forwards
    logging.info(
        "Linearly interpolating between missing vehicle counts of remaining detectors"
    )
    scoot_df["n_vehicles_in_interval"] = scoot_df["n_vehicles_in_interval"].interpolate(
        method="linear", limit_direction="both", axis=0
    )

    # User choice to run periodogram
    if drop_aperiodic:
        scoot_df = drop_aperiodic_detectors(scoot_df, fap_percentile_threshold)

    post_periodic_length = len(set(scoot_df.index.get_level_values("detector_id")))
    logging.info(
        "%d additional detectors dropped by periodicity checks",
        curr_length - post_periodic_length,
    )

    # Fill missing lon, lats, locations etc.
    proc_df = fill_missing_values(scoot_df)

    if readings_type:
        logging.info("%s data processing complete.", readings_type.upper())
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

    # Check here to see if any detectors are left!
    if dropped_df.empty:
        raise ValueError(
            "All detectors have too many anomalies. Try increasing the max_anom_per_day threshold."
        )
    return dropped_df


def drop_sparse_detectors(
    scoot_df: pd.DataFrame,
    end_times: np.ndarray,
    percentage_missing: int,
    consecutive_missing_threshold: int,
) -> pd.DataFrame:

    """Remove detectors from the dataframe with too many missing values over
    the time range of the input dataframe either globally or in local chunks.
    Args:
        scoot_df: Dataframe of scoot data (preferably free from anomalies)
        end_times: Array of measurement times for which we want measurements for.
        percentage_missing: A detector above percentage_missing of missing data
                             will be removed from the dataframe
        consecutive_missing_threshold: Max allowable amount of consecutive missing readings
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
        # Get array of missing vehicle count readings' status
        missing = scoot_df.loc[det]["n_vehicles_in_interval"].isna().astype(int)

        # Check for Sparsity
        is_sparse = missing.sum() > len(end_times) * 0.01 * percentage_missing

        # Check for consecutive missing values
        max_missing_consecutive = (
            missing.groupby((missing != missing.shift()).cumsum()).transform("size")
            * missing
        ).max()

        is_missing_consecutive = max_missing_consecutive > consecutive_missing_threshold

        if is_sparse or is_missing_consecutive:
            detectors_to_drop.append(det)

    logging.info(
        "Dropping detectors with > %d%% missing data or more than %d consecutive missing values",
        percentage_missing,
        consecutive_missing_threshold,
    )

    # If there are detectors to be dropped, remove them.
    if detectors_to_drop:
        scoot_df.drop(detectors_to_drop, level="detector_id", inplace=True)

    # Check here to see if any detectors are left!
    if scoot_df.empty:
        raise ValueError(
            "All detectors have been dropped. Try increasing percentage_missing and/or consecutive_missing_threshold."
        )

    return scoot_df


def fill_missing_values(scoot_df: pd.DataFrame) -> pd.DataFrame:

    """Fills the missing values of the remaining detectors with sufficiently low
    amounts of missing data.

    Args:
        scoot_df: DataFrame of SCOOT data with added rows representing missing readings
    Returns:
        scoot_df: Full SCOOT dataframe with interpolated/filled values.
    """

    # Create the remaining columns/fill missing row values
    logging.info("Padding the remaining columns with existing values")
    scoot_df["measurement_start_utc"] = scoot_df.index.get_level_values(
        "measurement_end_utc"
    ) - np.timedelta64(1, "h")
    scoot_df = scoot_df.reset_index()
    scoot_df.sort_values(["detector_id", "measurement_end_utc"], inplace=True)

    # Fill missing lon, lat, rolling, global columns with existing values
    scoot_df = scoot_df.groupby("detector_id").apply(lambda x: x.ffill().bfill())

    # ffill and bfill convert row and col to floats. Remedy that here
    scoot_df["row"] = scoot_df["row"].astype(int)
    scoot_df["col"] = scoot_df["col"].astype(int)

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


def fap(detector_timeseries: pd.DataFrame) -> float:

    """Find the false alarm probability for a given detector of having
    a dominant period in the range of 15 - 30 hours. By setting
    a threshold on this value, we can exclude sufficiently aperiodic
    detectors.
    Args:
        detector_timeseries: dataframe for single detector
    Returns:
        False alarm probability as float"""

    X = detector_timeseries.reset_index()
    X = X.drop(columns=["detector_id", "measurement_end_utc"])
    x = X.index.to_numpy()
    y = X.to_numpy().flatten()

    # Call astropy's LombScargle periodogram
    periodogram = LombScargle(x, y)
    period = np.linspace(15, 30, 300)

    # Find the most dominant period and its 'power' output
    pmax = periodogram.power(1 / period).max()
    # print(pmax)

    return periodogram.false_alarm_probability(pmax)


def drop_aperiodic_detectors(
    proc_df: pd.DataFrame, fap_percentile_threshold: float
) -> pd.DataFrame:

    """Drop all detectors that are not periodic 'enough' to continue with analysis.
    Helps drop badly-behaved detectors.
    Args:
        proc_df: Dataframe processed from anomalied and missing values
        fap_threshold: Detectors with false-alarm-probabilites greater than this
                       threshold will be removed. Note: the value of the threshold
                       depends on the number of data points passed to the periodogram.

    Returns:
        proc_df: Dataframe complete from processing.
    """

    proc_df = proc_df.join(
        proc_df.groupby(level="detector_id")["n_vehicles_in_interval"].apply(fap),
        on=["detector_id"],
        rsuffix="X",
    )

    # Rename 'wrongly' named column. Could be re-factored nicely
    proc_df.rename({"n_vehicles_in_intervalX": "fap"}, axis=1, inplace=True)

    # Drop the top 5% quantile of aperiodic detectors
    # Uses the assumption of "Most Scoot detctors are well behaved"
    fap_threshold = np.percentile(proc_df["fap"], fap_percentile_threshold * 100)

    # Return detectors which satisfy the condition
    proc_df = proc_df[proc_df["fap"] < fap_threshold]

    if proc_df.empty:
        error_message = "All detectors do not meet the periodicity requirements. "
        error_message += "Try increasing the fap percentile threshold."
        raise ValueError(error_message)

    return proc_df


def intersect_processed_data(
    processed_train, processed_test
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Ensures that both train and forecast dataframes contain data
    spanning the same set of detctors. Detector time series can be dropped
    in both sets of pre-processing. This additional step is required
    to ensure detectors exist in both.

    Args:
        processed_train: Processed training data
        processed_test: Processed test data
    Returns:
        processed_train, processed_forecast contaning data for the same detectors
    """

    common_detectors = set(processed_train["detector_id"]).intersection(
        set(processed_test["detector_id"])
    )

    return (
        processed_train[processed_train["detector_id"].isin(common_detectors)],
        processed_test[processed_test["detector_id"].isin(common_detectors)],
    )
