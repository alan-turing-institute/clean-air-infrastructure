"""
SCOOT feature extraction
"""
import argparse
import logging
from cleanair.loggers import get_log_level
from cleanair.features import ScootFeatures


def main():
    """
    Extract scoot features
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Extract scoot features")
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
        default=30,
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
    logging.basicConfig(level=get_log_level(args.verbose))

    # Extract features and notify any exceptions
    try:
        scoot_feature_extractor = ScootFeatures(ndays=args.ndays, end=args.end, secretfile=args.secretfile)

        # Construct SCOOT feature for each road using:
        # - the most recent SCOOT forecasts (from ScootForecast)
        # - the static association between roads and SCOOT sensors (from ScootRoadMatch)
        scoot_feature_extractor.test()
        # scoot_feature_extractor.update_remote_tables()

    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
