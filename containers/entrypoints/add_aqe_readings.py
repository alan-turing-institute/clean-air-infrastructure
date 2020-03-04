"""
Add AQE readings to database
"""
import argparse
from cleanair.inputs import AQEWriter
from cleanair.loggers import initialise_logging


def main():
    """
    Update AQE table
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Get AQE sensor data")
    parser.add_argument(
        "-e",
        "--end",
        type=str,
        default="yesterday",
        help="The last date (YYYY-MM-DD) to get data for.",
    )
    parser.add_argument(
        "-n",
        "--ndays",
        type=int,
        default=2,
        help="The number of days to request data for.",
    )
    parser.add_argument(
        "-s",
        "--secretfile",
        default="db_secrets.json",
        help="File with connection secrets.",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()
    if args.ndays < 1:
        raise argparse.ArgumentTypeError("Argument --ndays must be greater than 0")

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Perform update and notify any exceptions
    try:
        aqe_writer = AQEWriter(
            end=args.end, ndays=args.ndays, secretfile=args.secretfile
        )

        # Update the AQE tables on the database
        aqe_writer.update_remote_tables()
    except Exception as error:
        default_logger.error("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
