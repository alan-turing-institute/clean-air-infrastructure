from uatraffic import LockdownProcess


def main():

    lockdown_process = LockdownProcess(
        secretfile="/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json"
    )

    baseline_df = lockdown_process.get_scoot_with_location(
        start_time="2020-03-02", end_time="2020-03-03", output_type="df"
    )
    latest_df = lockdown_process.get_scoot_with_location(
        start_time="2020-04-06", end_time="2020-04-07", output_type="df"
    )
    baseline_gb = baseline_df.groupby("detector_id")
    latest_df = latest_df.groupby("detector")

    print(baseline_df.head())
    print(baseline_df["measurement_start_utc"].min(), baseline_df["measurement_start_utc"].max())


if __name__ == "__main__":
    main()
