"""
Update SCOOT database and run feature processing
"""
import argparse
import json
import logging
import os
from cleanair.inputs import ScootWriter
from cleanair.loggers import get_log_level
from cleanair.features import ScootFeatures


def main():
    """Update the scoot database"""
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Get Scoot traffic data")
    parser.add_argument("-e", "--end", type=str, default="yesterday",
                        help="The last date (YYYY-MM-DD) to get data for.")
    parser.add_argument("-i", "--aws-key-id", type=str, default="", help="AWS key ID for accessing TfL SCOOT data.")
    parser.add_argument("-k", "--aws-key", type=str, default="", help="AWS key for accessing TfL SCOOT data.")
    parser.add_argument("-n", "--ndays", type=int, default=1, help="The number of days to request data for.")
    parser.add_argument("-s", "--secretfile", default="db_secrets.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()
    if args.ndays < 1:
        raise argparse.ArgumentTypeError("Argument --ndays must be greater than 0")

    # Set logging verbosity
    kwargs = vars(args)
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # Perform update and notify any exceptions
    try:
        # Check that we have AWS connection information and try to retrieve it from a local secrets file if not
        if not (args.aws_key_id and args.aws_key):
            try:
                with open(os.path.join("/secrets", "aws_secrets.json")) as f_secret:
                    data = json.load(f_secret)
                    args.aws_key_id = data["aws_key_id"]
                    args.aws_key = data["aws_key"]
            except json.decoder.JSONDecodeError:
                raise argparse.ArgumentTypeError("Could not determine SCOOT aws_key_id or aws_key")

        # Update the Scoot readings table on the database
        scoot_writer = ScootWriter(**kwargs)
        scoot_writer.update_remote_tables()

        # Extract static features into the appropriate tables on the database
        # List which sources to process
        kwargs["sources"] = ["aqe", "laqn", "satellite", "grid_100"]
        static_feature_extractor = ScootFeatures(**kwargs)
        static_feature_extractor.update_scoot_road_reading(find_closest_roads=False)
        static_feature_extractor.update_remote_tables()

    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
