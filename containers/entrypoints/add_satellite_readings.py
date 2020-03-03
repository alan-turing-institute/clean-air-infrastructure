"""
Update SCOOT database
"""
import argparse
import json
import os
from cleanair.inputs import SatelliteWriter
from cleanair.loggers import initialise_logging


def main():
    """Update the scoot database"""
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Get Satellite data")
    parser.add_argument(
        "-k",
        "--copernicus-key",
        type=str,
        default="",
        help="copernicus key for accessing satellite data.",
    )
    parser.add_argument(
        "-e",
        "--end",
        type=str,
        default="today",
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
        "-i",
        "--interestpoints",
        dest="define_interest_points",
        action="store_true",
        help="""The first time satellite data is inserted into the database,
                        this flag must be set to insert the interest points""",
    )
    parser.add_argument(
        "-a",
        "--archive",
        dest="use_archive_data",
        action="store_true",
        help="""Use archive data rather than forecast data""",
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
        # Check that we have AWS connection information and try to retrieve it from a local secrets file if not
        if not args.copernicus_key:
            try:
                with open(
                    os.path.join("/secrets", "copernicus_secrets.json")
                ) as f_secret:
                    data = json.load(f_secret)
                    args.copernicus_key = data["copernicus_key"]
            except json.decoder.JSONDecodeError:
                raise argparse.ArgumentTypeError("Could not determine copernicus_key")

        satellite_writer = SatelliteWriter(copernicus_key=args.copernicus_key, end=args.end, ndays=args.ndays, secretfile=args.secretfile, archive=args.archive)

        # Update the Scoot readings table on the database
        satellite_writer.update_remote_tables()
    except Exception as error:
        default_logger.error("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
