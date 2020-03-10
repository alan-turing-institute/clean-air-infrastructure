"""
Run feature processing using UKMap data
"""
from cleanair.loggers import initialise_logging
from cleanair.features import UKMapFeatures
from cleanair.parsers import UKMapFeatureArgumentParser


def main():
    """
    Extract static UKMap features
    """
    # Parse and interpret command line arguments
    args = UKMapFeatureArgumentParser(description="Extract static UKMap features", sources=["aqe", "laqn", "satellite", "hexgrid"]).parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Update UKMap features on the database, logging any unhandled exceptions
    try:
        static_feature_extractor = UKMapFeatures(
            secretfile=args.secretfile, sources=args.sources
        )
        static_feature_extractor.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()
