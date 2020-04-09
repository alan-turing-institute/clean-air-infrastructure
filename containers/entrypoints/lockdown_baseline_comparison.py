
import pandas as pd

from uatraffic import LockdownProcess
from uatraffic import remove_outliers
from uatraffic import align_dfs_by_hour
from uatraffic import percent_of_baseline

def main():

    secretfile = "../../terraform/.secrets/db_secrets.json"
    lockdown_process = LockdownProcess(
        secretfile=secretfile
    )

    # get data from database
    baseline_df = lockdown_process.get_scoot_with_location(
        start_time="2020-03-02", end_time="2020-03-03", output_type="df"
    )
    latest_df = lockdown_process.get_scoot_with_location(
        start_time="2020-03-31", end_time="2020-04-01", output_type="df"
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

    print(metric_df)

if __name__ == "__main__":
    main()
