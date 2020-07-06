"""
Run feature processing using SCOOT readings
"""
from cleanair.loggers import initialise_logging
from cleanair.features import ScootReadingFeatures
from cleanair.processors import ScootPerRoadReadingMapper
from cleanair.parsers import ScootReadingFeatureArgumentParser


def main():
    """
    Convert SCOOT readings into features
    """
    # Parse and interpret command line arguments
    args = ScootReadingFeatureArgumentParser(
        description="Extract model features from SCOOT readings",
        sources=["satellite", "hexgrid"],
    ).parse_args()

    # Set some parameters using the parsed arguments
    default_logger = initialise_logging(args.verbose)

    # Update SCOOT reading features on the database, logging any unhandled exceptions
    try:
        # Construct SCOOT readings for each road using:
        # - the relevant SCOOT readings (from ScootWriter)
        # - the static association between roads and SCOOT sensors (from ScootRoadMatch)
        scoot_road_readings = ScootPerRoadReadingMapper(
            nhours=args.nhours, end=args.upto, secretfile=args.secretfile
        )
        scoot_road_readings.update_remote_tables()

        # Construct SCOOT features from readings around each interest point
        scoot_feature_extractor = ScootReadingFeatures(
            batch_size=500,
            nhours=args.nhours,
            end=args.upto,
            secretfile=args.secretfile,
        )
        scoot_feature_extractor.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()
