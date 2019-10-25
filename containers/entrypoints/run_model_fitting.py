"""
UKMap Feature extraction
"""
import argparse
import logging
from cleanair.loggers import get_log_level
from cleanair.models import ModelFitting


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
       model_fit = ModelFitting(**kwargs)
       model_fit.get_model_fit_input(start_date='2019-10-12', end_date='2019-10-13', sources=['laqn', 'aqe']).to_csv('/secrets/model_data.csv')

    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
