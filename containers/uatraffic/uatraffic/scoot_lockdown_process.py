"""GLA Scoot lockdown processing"""
import datetime
import logging
import time
import pandas as pd
from sqlalchemy import func
from cleanair.databases import DBWriter
from cleanair.decorators import db_query
from cleanair.databases.tables import (
    ScootReading,
    ScootForecast,
    MetaPoint,
    ScootDetector,
)
from cleanair.decorators import SuppressStdoutStderr
from cleanair.loggers import duration, duration_from_seconds, get_logger, green


class LockdownProcess(DBWriter):
    """Lockdown processing for GLA"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        self.baseline_df = None
        self.latest_df = None
        self.baseline_gb = None
        self.latest_gb = None

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    def percent_of_normal(
        self, groupby_cols=["detector_id"], debug=False, ignore_missing=False,
    ):
        """Group both dataframes by detector id and day then """
        try:
            normal_set = set(self.baseline_df.detector_id)
            latest_set = set(self.latest_df.detector_id)
            assert normal_set == latest_set
        except AssertionError:
            logging.warning(
                "normal_df and latest_df have different sensors. Trying to compensate."
            )
        finally:
            detector_set = normal_set.intersection(latest_set)

        # groupby columns, by default detector id
        normal_gb = self.baseline_df.groupby(groupby_cols)
        latest_gb = self.latest_df.groupby(groupby_cols)

        # keep results in a dataframe
        value_cols = ["normal_sum", "latest_sum", "percent_of_normal"]
        rows_list = []
        normal_zero_count = []
        latest_zero_count = []
        different_count = []

        for name, group in normal_gb:
            if name in detector_set:
                try:
                    assert list(group["hour"].sort_values()) == list(
                        latest_gb.get_group(name)["hour"].sort_values()
                    )
                except AssertionError:
                    if ignore_missing:
                        different_count.append(name)
                    else:
                        raise ValueError(
                            "Both dataframes should have the same entries for each hour. See align_dfs_by_hour()."
                        )

                # sum all vehicles in the normal day for this detector
                normal_sum = group["n_vehicles_in_interval"].sum()
                try:
                    assert normal_sum > 0
                except AssertionError:
                    logging.debug(
                        "Normal sum is not greater than zero for detector %s. Setting normal sum to 1.",
                        name,
                    )
                    normal_zero_count.append(name)
                    normal_sum = 1

                # sum all vehicles in the latest day for this detector
                # ToDo: is this oK to set to 1?
                latest_sum = latest_gb.get_group(name)["n_vehicles_in_interval"].sum()
                try:
                    assert latest_sum > 0
                except AssertionError:
                    logging.debug(
                        "Latest sum is not greater than zero for detector %s. Setting latest sum to 1.",
                        name,
                    )
                    latest_zero_count.append(name)
                    latest_sum = 1

                percent_change = 100 - 100 * (normal_sum - latest_sum) / normal_sum

                if len(groupby_cols) > 1:
                    index_dict = {
                        groupby_cols[i]: name[i] for i in range(len(groupby_cols))
                    }
                else:
                    index_dict = {groupby_cols[0]: name}

                row_dict = dict(
                    index_dict,
                    normal_sum=normal_sum,
                    latest_sum=latest_sum,
                    percent_of_normal=percent_change,
                )
                rows_list.append(row_dict)

        logging.info(
            "%s detectors with zero vehicles in normal", len(normal_zero_count)
        )
        logging.info(
            "%s detectors with zero vehicles in latest", len(latest_zero_count)
        )
        logging.info(
            "%s detectors with different number of observations.", len(different_count)
        )
        return pd.DataFrame(rows_list)

    def align_dfs_by_hour(self, df1, df2):
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

    @db_query
    def get_scoot_with_location(self, start_time, end_time=None):
        """
        Get scoot data with lat and long positions
        """

        with self.dbcnxn.open_session() as session:
            scoot_readings = (
                session.query(
                    ScootReading.detector_id,
                    func.ST_X(MetaPoint.location).label("lon"),
                    func.ST_Y(MetaPoint.location).label("lat"),
                    ScootReading.measurement_start_utc,
                    ScootReading.measurement_end_utc,
                    ScootReading.n_vehicles_in_interval,
                )
                .join(
                    ScootDetector, ScootReading.detector_id == ScootDetector.detector_n
                )
                .join(MetaPoint, MetaPoint.id == ScootDetector.point_id)
                .filter(ScootReading.measurement_start_utc >= start_time)
            )

            if end_time:

                scoot_readings = scoot_readings.filter(
                    ScootReading.measurement_start_utc < end_time
                )

            scoot_readings = scoot_readings.order_by(
                ScootReading.detector_id, ScootReading.measurement_start_utc
            )

            return scoot_readings


def remove_outliers(df, k=3, col="n_vehicles_in_interval"):
    """Remove outliers $x$ where $|x - \mu| > k \sigma$ for each detector."""
    to_remove = get_index_of_outliers(df, k=3, col=col)
    logging.info("Removed %s anomalous readings.", len(to_remove))
    logging.info("Total %s readings.", len(df))
    return df.loc[~df.index.isin(set(to_remove))]


def get_index_of_outliers(df, k=3, col="n_vehicles_in_interval"):
    """Returns a list of indices that are outliers."""
    # remove outliers
    to_remove = []  # list of indices to remove

    # groupby detector
    gb = df.groupby("detector_id")

    for detector_id, group in gb:
        remove_in_group = group.index[
            abs(group[col] - group[col].mean()) > k * group[col].std()
        ].tolist()
        to_remove.extend(remove_in_group)
    return to_remove
