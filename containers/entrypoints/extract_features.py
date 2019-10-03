"""
UKMap Feature extraction
"""
import argparse
import logging
from cleanair.loggers import get_log_level
from cleanair.features import FeatureExtractor


def main():
    """
    Extract features
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Get LAQN sensor data")
    parser.add_argument("-s", "--secretfile", default="db_secrets.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()

    # Set logging verbosity
    kwargs = vars(args)
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    # List which sources to process
    kwargs["sources"] = ["aqe", "laqn"]

    # Extract features and notify any exceptions
    try:
        feature_extractor = FeatureExtractor(**kwargs)

        # Update feature tables on the database
        feature_extractor.update_remote_tables()
    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise

if __name__ == '__main__':
    main()
