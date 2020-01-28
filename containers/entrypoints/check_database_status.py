"""
CLI to check what is in the cleanair database
"""
import logging
import argparse
from dateutil.parser import isoparse
from dateutil.relativedelta import relativedelta
from cleanair.mixins import DBStatus
from cleanair.loggers import get_log_level


def main():
    """
    CleanAir database queries
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Run model fitting")
    parser.add_argument(
        "-s",
        "--secretfile",
        default="db_secrets.json",
        help="File with connection secrets.",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()
    kwargs = vars(args)

    # Set logging verbosity
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # Print database information
    database_status = DBStatus(**kwargs)

    # print(database_status.get_available_static_features(output_type='df'))
    # print(database_status.get_available_interest_points()
    print(database_status.get_available_static_features_by_source(output_type="df"))

    # print(database_status.get_available_dynamic_features(start_date='2020-01-01', end_date='2020-01-05', output_type='df'))
    # print(database_status.get_available_sources(output_type='df'))
    # print(database_status.get_available_interest_points(sources=['laqn', 'aqe'], output_type='df'))


if __name__ == "__main__":
    main()
