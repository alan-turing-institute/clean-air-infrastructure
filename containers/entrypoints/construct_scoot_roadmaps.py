"""
SCOOT road-sensor association
"""
import argparse
import logging
from cleanair.loggers import get_log_level
from cleanair.features import ScootRoadMapper


def main():
    """
    Extract scoot features
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Extract scoot features")
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
    logging.basicConfig(level=get_log_level(args.verbose))

    # Extract features and notify any exceptions
    try:
        road_mapper = ScootRoadMapper(secretfile=args.secretfile)

        # Match all road segments to their closest SCOOT detector(s)
        # - if the segment has detectors on it then match to them
        # - otherwise match to the five closest detectors
        road_mapper.update_remote_tables()

    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
