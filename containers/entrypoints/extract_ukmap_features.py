"""
UKMap Feature extraction
"""
import argparse
from cleanair.loggers import initialise_logging
from cleanair.features import UKMapFeatures


def main():
    """
    Extract static features
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Extract static UKMap features")
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
        static_feature_extractor = UKMapFeatures(secretfile=args.secretfile, sources=args.sources)
        static_feature_extractor.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
