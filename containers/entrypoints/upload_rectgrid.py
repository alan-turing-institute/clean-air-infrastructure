"""
Upload static datasets
"""
import argparse
from cleanair.inputs import RectGridWriter
from cleanair.loggers import initialise_logging


def main():
    """
    Upload square grid data
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Insert static datasets")
    parser.add_argument(
        "-s",
        "--secretfile",
        default="db_secrets.json",
        help="File with connection secrets.",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Perform update and notify any exceptions
    try:
        rectgrid_writer = RectGridWriter(secretfile=args.secretfile)

        # Upload the rectangular grid table to the database if it is not present
        rectgrid_writer.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
