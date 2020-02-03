"""
Scoot Feature extraction
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
    kwargs = vars(args)
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # List which sources to process
    kwargs["sources"] = ["aqe", "laqn", "satellite", "grid_100"]

    # Extract features and notify any exceptions
    try:
        static_feature_extractor = ScootFeatures(**kwargs)
        # Extract static features into the appropriate tables on the database
        static_feature_extractor.update_scoot_road_reading(find_closest_roads=False)
        static_feature_extractor.update_remote_tables()

    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
