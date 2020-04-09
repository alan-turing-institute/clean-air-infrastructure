
import logging
from datetime import date
import pandas as pd

from cleanair.databases.tables import ScootPercentChange

from uatraffic import LockdownProcess
from uatraffic import remove_outliers
from uatraffic import align_dfs_by_hour
from uatraffic import percent_of_baseline

def main():

    secretfile = "../../terraform/.secrets/db_secrets.json"
    lockdown_process = LockdownProcess(
        secretfile=secretfile
    )

    latest_start = "2020-03-31"
    latest_end = "2020-04-01"

    # get a range of dates over 3 weeks for normal period, starting from 10th Feb

    # split up by weekday (0 Monday, 1 Tuesday)

    # remove zeros to avoid skewing the median

    # take the median for each hour of each weekday


    # get data from database
    baseline_df = lockdown_process.get_scoot_with_location(
        start_time="2020-03-02", end_time="2020-03-03", output_type="df"
    )
    latest_df = lockdown_process.get_scoot_with_location(
        start_time=latest_start, end_time=latest_end, output_type="df"
    )
    # add an hour column
    baseline_df["hour"] = pd.to_datetime(baseline_df.measurement_start_utc).dt.hour
    latest_df["hour"] = pd.to_datetime(latest_df.measurement_start_utc).dt.hour

    # get stats
    print(baseline_df.head())
    print(baseline_df["measurement_start_utc"].min(), baseline_df["measurement_start_utc"].max())

    # remove outliers and align for missing values
    baseline_df = remove_outliers(baseline_df)
    latest_df = remove_outliers(latest_df)
    baseline_df, latest_df = align_dfs_by_hour(baseline_df, latest_df)

    # calculate the percent of latest traffic from local traffic
    metric_df = percent_of_baseline(baseline_df, latest_df)

    metric_df["latest_start_utc"] = latest_start
    metric_df["latest_end_utc"] = latest_end
    metric_df["day_of_week"] = date.fromisoformat('2020-01-01').weekday()
    metric_df["baseline_period"] = "normal"     # ToDo: remove hardcoding

    print(metric_df)

    record_cols = [
        "detector_id",
        "latest_start_utc",
        "latest_end_utc",
        "day_of_week",
        "baseline_period",
        "baseline_n_vehicles_in_interval",
        "latest_n_vehicles_in_interval",
        "percent_of_baseline",
        # "lat",
        # "lon"
    ]

    upload_records = metric_df[record_cols].to_dict("records")
    logging.info("Inserting %s records into the database", len(upload_records))
    with lockdown_process.dbcnxn.open_session() as session:
        lockdown_process.commit_records(
            session, upload_records, table=ScootPercentChange, on_conflict="overwrite"
        )

if __name__ == "__main__":
    main()
