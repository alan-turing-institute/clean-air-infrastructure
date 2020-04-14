"""
Calculate the percent of baseline metric for a recent day.
"""
import logging
from datetime import date, datetime, timedelta
import pandas as pd

from cleanair.databases.tables import ScootPercentChange

from uatraffic.databases import TrafficQuery
from uatraffic.preprocess import remove_outliers
from uatraffic.preprocess import align_dfs_by_hour
from uatraffic.metric import percent_of_baseline
from uatraffic.util import BaselineParser

def main():

    # get args from parser
    parser = BaselineParser(nhours=24)
    args = parser.parse_args()

    # get query object
    lockdown_process = TrafficQuery(
        secretfile=args.secretfile
    )

    # the end of the latest day is latest_start + nhours
    latest_end = datetime.strptime(args.latest_start, "%Y-%m-%d") + timedelta(hours=args.nhours)

    # get the day of week for the latest day
    day_of_week = date.fromisoformat(args.latest_start).weekday()
    assert day_of_week >= 0 and day_of_week < 7

    # get data from database for the given day_of_week
    baseline_df = lockdown_process.get_scoot_filter_by_dow(
        start_time=args.baseline_start,
        end_time=args.baseline_end,
        day_of_week=day_of_week,
        output_type="df"
    )
    latest_df = lockdown_process.get_scoot_with_location(
        start_time=args.latest_start, end_time=latest_end, output_type="df"
    )
    # add an hour column
    baseline_df["hour"] = pd.to_datetime(baseline_df.measurement_start_utc).dt.hour
    latest_df["hour"] = pd.to_datetime(latest_df.measurement_start_utc).dt.hour

    # remove outliers and align for missing values
    baseline_df = remove_outliers(baseline_df)
    latest_df = remove_outliers(latest_df)

    # calculate the percent of latest traffic from local traffic
    metric_df = percent_of_baseline(baseline_df, latest_df)
    metric_df["latest_start_utc"] = args.latest_start
    metric_df["latest_end_utc"] = latest_end
    metric_df["day_of_week"] = day_of_week
    metric_df["baseline_period"] = args.tag

    # upload records to database
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
