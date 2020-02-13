"""
SCOOT feature extraction
"""
import argparse
import logging
from cleanair.loggers import get_log_level
from cleanair.features import ScootMapToRoads, ScootFeatures


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
        static_feature_extractor = ScootFeatures(ndays=args.ndays, end=args.end, secretfile=args.secretfile)
        road_mapper = ScootMapToRoads(secretfile=args.secretfile)

        # Match all road segments to their closest SCOOT detector(s)
        # - if the segment has a detector on it then match to one
        # - otherwise match to the five closest detectors
        road_mapper.match_to_roads()



        # Insert closest roads and calculate inverse distance
        # static_feature_extractor.insert_closest_roads()

        # Check what is in the database
        # static_feature_extractor.update_remote_tables()
        # print(static_feature_extractor.get_last_scoot_road_reading(
        #     static_feature_extractor.start_datetime, static_feature_extractor.end_datetime, output_type='list'))
        # Match roads

        # print(static_feature_extractor.join_scoot_with_road(output_type='df'))
        # print(static_feature_extractor.join_unmatached_scoot_with_road(output_type='df'))
        # print(static_feature_extractor.total_inverse_distance(output_type='df'))

        # # Extract static features into the appropriate tables on the database
        # static_feature_extractor.update_scoot_road_reading_tables(
        #     find_closest_roads=False
        # )
        # static_feature_extractor.update_remote_tables()

    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
