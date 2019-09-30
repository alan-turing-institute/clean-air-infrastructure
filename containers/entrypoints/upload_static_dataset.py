"""
Upload static datasets
"""
import argparse
import logging
from cleanair.inputs import StaticWriter
from cleanair.loggers import get_log_level


def main():
    """
    Upload static datasets
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Insert static datasets")
    parser.add_argument("-s", "--secretfile", default="db_secrets.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()

    # Set logging verbosity
    kwargs = vars(args)
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # Perform update and notify any exceptions
    try:
        static_writer = StaticWriter(**kwargs)

        # Upload static tables to the database if they are not present
        static_writer.update_remote_tables()

    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
