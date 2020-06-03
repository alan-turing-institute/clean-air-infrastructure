"""
Construct SCOOT road-sensor association
"""
from cleanair.loggers import initialise_logging
from cleanair.processors import ScootPerRoadDetectors
from cleanair.parsers import ScootRoadmapArgumentParser


def main():
    """
    Construct maps between roads and SCOOT detectors
    """
    # Parse and interpret command line arguments
    args = ScootRoadmapArgumentParser(
        description="Construct maps between roads and SCOOT detectors"
    ).parse_args()

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Update the SCOOT roadmap table on the database, logging any unhandled exceptions
    try:
        road_mapper = ScootPerRoadDetectors(secretfile=args.secretfile)
        # Match all road segments to their closest SCOOT detector(s)
        # - if the segment has detectors on it then match to them
        # - otherwise match to the five closest detectors
        road_mapper.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise


if __name__ == "__main__":
    main()
