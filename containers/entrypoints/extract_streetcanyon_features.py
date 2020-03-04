"""
Run feature processing using StreetCanyon data
"""
import argparse
from cleanair.loggers import initialise_logging
from cleanair.features import StreetCanyonFeatures


def main():
    """
    Extract static StreetCanyon features
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Extract static StreetCanyon features")
    parser.add_argument(
        "-s",
        "--secretfile",
        default="db_secrets.json",
        help="File with connection secrets.",
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["aqe", "laqn", "satellite", "hexgrid"],
        help="List of sources to process, (default: 'aqe', 'laqn', 'satellite', 'hexgrid').",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Extract features and notify any exceptions
    try:
        static_feature_extractor = StreetCanyonFeatures(
            secretfile=args.secretfile, sources=args.sources
        )
        # Extract static features into the appropriate tables on the database
        static_feature_extractor.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()
