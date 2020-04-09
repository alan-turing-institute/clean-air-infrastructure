from uatraffic import LockdownProcess


def main():

    lockdown_process = LockdownProcess(
        secretfile="/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json"
    )

    print(lockdown_process.get_scoot_with_location("2020-03-01", output_type="df"))


if __name__ == "__main__":
    main()
