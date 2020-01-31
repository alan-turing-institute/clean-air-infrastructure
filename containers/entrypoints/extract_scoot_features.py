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
        default="yesterday",
        help="The last date (YYYY-MM-DD) to get data for.",
    )
    parser.add_argument(
        "-n",
        "--ndays",
        type=int,
<<<<<<< HEAD
        default=2,
=======
        default=1,
>>>>>>> f832593... Dont exclude features based on id if dynamic
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

    # Extract features and notify any exceptions
    try:
        # Map scoot features to roads/
        scoot_road_map = ScootMapToRoads(**kwargs)
        # # scoot_road_map.insert_closest_roads() #Needs to run first
        # scoot_road_map.update_remote_tables()

        # Process features
        kwargs["sources"] = ["aqe", "laqn", "satellite", "grid_100"]
        scoot_feature_extractor = ScootFeatures(**kwargs)
        # Extract static features into the appropriate tables on the database
        static_feature_extractor.update_scoot_road_reading(find_closest_roads=False)
        static_feature_extractor.update_remote_tables()

        # Clean up
        scoot_road_map.delete_remote_entries()

    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
