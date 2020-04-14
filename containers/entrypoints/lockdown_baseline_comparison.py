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

    # the end of the comparison day is comparison_start + nhours
    comparison_end = datetime.strptime(args.comparison_start, "%Y-%m-%d") + timedelta(hours=args.nhours)

    # get the day of week for the comparison day
    day_of_week = date.fromisoformat(args.comparison_start).weekday()
    assert day_of_week >= 0 and day_of_week < 7

    # get data from database for the given day_of_week
    baseline_df = lockdown_process.get_scoot_filter_by_dow(
        start_time=args.baseline_start,
        end_time=args.baseline_end,
        day_of_week=day_of_week,
        output_type="df"
    )
    comparison_df = lockdown_process.get_scoot_with_location(
        start_time=args.comparison_start, end_time=comparison_end, output_type="df"
    )
    # add an hour column
    baseline_df["hour"] = pd.to_datetime(baseline_df.measurement_start_utc).dt.hour
    comparison_df["hour"] = pd.to_datetime(comparison_df.measurement_start_utc).dt.hour
    baseline_anomaly_df = baseline_df.copy()
    comparison_anomaly_df = comparison_df.copy()

    # remove outliers and align for missing values
    baseline_df = remove_outliers(baseline_df)
    comparison_df = remove_outliers(comparison_df)

    # get dataframes of anomalous readings
    # TODO: check nots they are the wrong way round!
    baseline_anomaly_df = baseline_anomaly_df.loc[~baseline_anomaly_df.index.isin(baseline_df)]
    comparison_anomaly_df = comparison_anomaly_df.loc[~comparison_anomaly_df.index.isin(comparison_df)]

    # TODO: add flags for each detector for anomalies
    # removed_anomaly_in_baseline = False,
    # removed_anomaly_in_comparison = False,

    # calculate the percent of comparison traffic from local traffic
    metric_df = percent_of_baseline(baseline_df, comparison_df)
    print(metric_df)
    metric_df["measurement_start_utc"] = args.comparison_start
    metric_df["measurement_end_utc"] = comparison_end
    metric_df["day_of_week"] = day_of_week
    metric_df["baseline_period"] = args.tag
    metric_df["removed_anomaly_from_baseline"] = metric_df["detector_id"].isin(baseline_anomaly_df["detector_id"].unique())
    metric_df["removed_anomaly_from_comparison"] = metric_df["detector_id"].isin(comparison_anomaly_df["detector_id"].unique())

    # upload records to database
    record_cols = [
        "detector_id",
        "measurement_start_utc",
        "measurement_end_utc",
        "day_of_week",
        "baseline_period",
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
    logging.info("Inserting %s records into the database", len(upload_records))
    with lockdown_process.dbcnxn.open_session() as session:
        lockdown_process.commit_records(
            session, upload_records, table=ScootPercentChange, on_conflict="overwrite"
        )

if __name__ == "__main__":
    main()
