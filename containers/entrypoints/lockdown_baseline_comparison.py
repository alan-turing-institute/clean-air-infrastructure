from uatraffic import LockdownProcess


def main():

    lockdown_process = LockdownProcess(
        secretfile="/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json"
    )

    df = lockdown_process.get_scoot_with_location(
        start_time="2020-03-01", end_time="2020-03-02", output_type="df"
    )

    print(df.head())
    print(df["measurement_start_utc"].min(), df["measurement_start_utc"].max())

    print(
        lockdown_process.get_scoot_with_location(
            start_time="2020-03-01", end_time="2020-03-02", output_type="sql"
        )
    )


if __name__ == "__main__":
    main()
