"""
Run feature processing using OSHighway data
"""
from cleanair.loggers import initialise_logging
from cleanair.features import OSHighwayFeatures
from cleanair.parsers import OsHighwayFeatureArgumentParser


def main():
    """
    Extract static OSHighway features
    """
    # Parse and interpret command line arguments
    args = OsHighwayFeatureArgumentParser(
        description="Extract static OSHighway features",
        sources=["aqe", "laqn", "satellite", "hexgrid"],
    ).parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Update OSHighway features on the database, logging any unhandled exceptions
    try:
        static_feature_extractor = OSHighwayFeatures(
            secretfile=args.secretfile, sources=args.sources
        )
        # Extract static features into the appropriate tables on the database
        static_feature_extractor.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()
