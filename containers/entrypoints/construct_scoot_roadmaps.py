"""
Construct SCOOT road-sensor association
"""
import argparse
from cleanair.loggers import initialise_logging
from cleanair.features import ScootRoadMapper


def main():
    """
    Construct maps between roads and SCOOT detectors
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(
        description="Construct maps between roads and SCOOT detectors"
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

    # Set logging verbosity
    default_logger = initialise_logging(args.verbose)

    # Extract features and notify any exceptions
    try:
        road_mapper = ScootRoadMapper(secretfile=args.secretfile)

        # Match all road segments to their closest SCOOT detector(s)
        # - if the segment has detectors on it then match to them
        # - otherwise match to the five closest detectors
        road_mapper.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
