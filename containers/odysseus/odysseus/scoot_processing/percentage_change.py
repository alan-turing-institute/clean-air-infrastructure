"""
Class for querying traffic and scoot data.
"""

from datetime import timedelta
import calendar
from dateutil import rrule
import pandas as pd

from cleanair.databases import DBWriter
from cleanair.mixins import DateRangeMixin, ScootQueryMixin
from cleanair.loggers.logcolours import green, red
from cleanair.databases.tables import (
    ScootReading,
    ScootPercentChange,
)
from cleanair.decorators import db_query
from cleanair.loggers import get_logger

from ..dates import (
    NORMAL_BASELINE_START,
    NORMAL_BASELINE_END,
    LOCKDOWN_BASELINE_START,
    LOCKDOWN_BASELINE_END,
)
from ..preprocess import remove_outliers
from ..metric import percent_of_baseline


class TrafficPercentageChange(DateRangeMixin, ScootQueryMixin, DBWriter):
    """
    Queries to run on the SCOOT DB.
    """

    def __init__(self, baseline_tag, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.baseline_tag = baseline_tag

        if baseline_tag == "normal":
            self.baseline_start = NORMAL_BASELINE_START
            self.baseline_end = NORMAL_BASELINE_END
        elif baseline_tag == "lockdown":
            self.baseline_start = LOCKDOWN_BASELINE_START
            self.baseline_end = LOCKDOWN_BASELINE_END
        else:
            raise ValueError("baseline_tag must be 'normal' or 'lockdown'")

    @db_query
    def get_percent_of_baseline(
        self, baseline_period, comparison_start, comparison_end=None, detectors=None
    ):
        """
        Get the values for the percent_of_baseline metric for a day and baseline.
        """
        with self.dbcnxn.open_session() as session:
            baseline_readings = (
                session.query(ScootPercentChange)
                .filter(ScootPercentChange.baseline_period == baseline_period)
                .filter(ScootPercentChange.measurement_start_utc >= comparison_start)
            )
            if comparison_end:
                baseline_readings = baseline_readings.filter(
                    ScootPercentChange.measurement_start_utc < comparison_end
                )
            # get subset of detectors
            if detectors:
                baseline_readings = baseline_readings.filter(
                    ScootReading.detector_id.in_(detectors)
                )
            return baseline_readings

    def percent_of_baseline(self, comparison_start_date):
        """Calculate the percentage of baseline"""
        # the end of the comparison day is comparison_start + nhours
        comparison_end_date = comparison_start_date + timedelta(days=1)

        # get the day of week for the comparison day
        day_of_week = comparison_start_date.weekday()

        self.logger.info(
            "Comparing scoot data from %s to all %s's between %s baseline. Baseline dates: %s to %s (exclusive)",
            green(comparison_start_date.isoformat()),
            green(calendar.day_name[day_of_week]),
            green(self.baseline_tag),
            green(self.baseline_start),
            green(self.baseline_end),
        )

        # get data from database for the given day_of_week
        baseline_df = self.get_scoot_by_dow(
            start_time=self.baseline_start,
            end_time=self.baseline_end,
            day_of_week=day_of_week,
            output_type="df",
            error_empty=True,
        )
        comparison_df = self.get_scoot_with_location(
            start_time=comparison_start_date.isoformat(),
            end_time=comparison_end_date.isoformat(),
            output_type="df",
            error_empty=True,
        )

        # add an hour column
        baseline_df["hour"] = pd.to_datetime(baseline_df.measurement_start_utc).dt.hour
        comparison_df["hour"] = pd.to_datetime(
            comparison_df.measurement_start_utc
        ).dt.hour
        baseline_anomaly_df = baseline_df.copy()
        comparison_anomaly_df = comparison_df.copy()

        # remove outliers and align for missing values
        baseline_df = remove_outliers(baseline_df)
        comparison_df = remove_outliers(comparison_df)

        # get dataframes of anomalous readings
        baseline_anomaly_df = baseline_anomaly_df.loc[
            ~baseline_anomaly_df.index.isin(baseline_df.index)
        ]
        comparison_anomaly_df = comparison_anomaly_df.loc[
            ~comparison_anomaly_df.index.isin(comparison_df.index)
        ]

        self.logger.info(
            "Number of anomalies in baseline is %s", len(baseline_anomaly_df)
        )
        self.logger.info(
            "Number of anomalies in comparison is %s", len(comparison_anomaly_df)
        )

        # calculate the percent of comparison traffic from local traffic
        self.logger.info("Calculating the percent of baseline metric.")
        metric_df = percent_of_baseline(baseline_df, comparison_df)

        self.logger.info("Writing percent of baseline metrics to database.")
        metric_df["measurement_start_utc"] = comparison_start_date
        metric_df["measurement_end_utc"] = comparison_end_date
        metric_df["day_of_week"] = day_of_week
        metric_df["baseline_period"] = self.baseline_tag
        metric_df["removed_anomaly_from_baseline"] = metric_df["detector_id"].isin(
            baseline_anomaly_df["detector_id"].unique()
        )
        metric_df["removed_anomaly_from_comparison"] = metric_df["detector_id"].isin(
            comparison_anomaly_df["detector_id"].unique()
        )

        metric_df["baseline_start_date"] = self.baseline_start
        metric_df["baseline_end_date"] = self.baseline_end

        return metric_df

    def update_remote_tables(self):

        self.logger.info(
            "Processing scoot data from %s to %s for %s baseline. Baseline dates: %s to %s (exclusive)",
            red(self.start_date.isoformat()),
            red(self.end_date.isoformat()),
            red(self.baseline_tag),
            red(self.baseline_start),
            red(self.baseline_end),
        )
        # Process one day at a time
        for comparison_date in rrule.rrule(
            rrule.DAILY, dtstart=self.start_date, until=self.end_date
        ):

            metric_df = self.percent_of_baseline(comparison_date.date())

            # upload records to database
            record_cols = [
                "detector_id",
                "measurement_start_utc",
                "measurement_end_utc",
                "day_of_week",
                "baseline_period",
                "baseline_start_date",
                "baseline_end_date",
                "baseline_n_vehicles_in_interval",
                "comparison_n_vehicles_in_interval",
                "percent_of_baseline",
                "no_traffic_in_baseline",
                "no_traffic_in_comparison",
                "low_confidence",
                "num_observations",
                "removed_anomaly_from_baseline",
                "removed_anomaly_from_comparison",
            ]

            upload_records = metric_df[record_cols].to_dict("records")

            self.commit_records(
                upload_records, on_conflict="overwrite", table=ScootPercentChange
            )
