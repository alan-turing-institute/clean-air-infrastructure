from cleanair.cleanair.databases import DBReader


class CovidTracker(DBReader):
    def __init__(self, **kwargs):

        super().__init__(**kwargs)


if __name__ == "__main__":

    covid = CovidTracker(
        secretfile="/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json"
    )
