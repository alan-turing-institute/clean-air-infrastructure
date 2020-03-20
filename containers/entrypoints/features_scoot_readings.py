"""
Run feature processing using SCOOT readings
"""
import argparse
from cleanair.loggers import initialise_logging
from cleanair.features import ScootReadingFeatures
from cleanair.processors import ScootPerRoadReadingMapper


def main():
    """
    Convert SCOOT readings into features
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Forecast SCOOT readings")
    parser.add_argument(
        "-s",
        "--secretfile",
        default="db_secrets.json",
        help="File containing connection secrets, (default: 'db_secrets.json').",
    )
    parser.add_argument(
        "-e",
        "--end",
        type=str,
        default="now",
        help="The last datetime (YYYY-MM-DD HH:MM:SS) to get data for, (default: 'now').",
    )
    parser.add_argument(
        "-n",
        "--ndays",
        type=int,
        default=2,
        help="The number of days into the past to calculate features for.",
    )

    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()
    if args.ndays < 1:
        raise argparse.ArgumentTypeError("Argument --ndays must be greater than 0")

    # Set some parameters using the parsed arguments
    default_logger = initialise_logging(args.verbose)

    # Perform update and notify any exceptions
    try:
        # Construct SCOOT readings for each road using:
        # - the relevant SCOOT readings (from ScootWriter)
        # - the static association between roads and SCOOT sensors (from ScootRoadMatch)
        scoot_road_readings = ScootPerRoadReadingMapper(
            ndays=args.ndays, end=args.end, secretfile=args.secretfile
        )
        scoot_road_readings.update_remote_tables()

        # Construct SCOOT features from readings around each interest point
        scoot_feature_extractor = ScootReadingFeatures(
            batch_size=1000, ndays=args.ndays, end=args.end, secretfile=args.secretfile,
        )
        scoot_feature_extractor.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()
