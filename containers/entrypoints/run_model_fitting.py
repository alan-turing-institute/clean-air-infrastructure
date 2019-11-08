"""
UKMap Feature extraction
"""
import sys
sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/containers/')
import argparse
import logging
from cleanair.loggers import get_log_level
from cleanair.models import ModelData


def main():
    """
    Extract static features
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Run model fitting")
    parser.add_argument("-s", "--secretfile", default="db_secrets.json", help="File with connection secrets.")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()

    # Set logging verbosity
    kwargs = vars(args)
    logging.basicConfig(level=get_log_level(kwargs.pop("verbose", 0)))

    try:
       model_fit = ModelData(**kwargs)
       model_fit.get_model_inputs(start_date='2019-10-25 00:00:00', end_date='2019-11-05 00:00:00', norm_by='laqn', sources=['laqn', 'aqe'], species=['NO2'])
    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
