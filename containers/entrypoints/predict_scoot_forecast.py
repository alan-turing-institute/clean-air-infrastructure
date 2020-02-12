"""
Model fitting
"""
import logging
import argparse
from cleanair.models import TrafficForecast
from cleanair.loggers import get_log_level


def main():
    """
    Predict SCOOT forecast
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Forecast SCOOT readings")
    parser.add_argument(
        "-s",
        "--secretfile",
        default="db_secrets.json",
        help="File with connection secrets.",
    )
    parser.add_argument(
        "-e",
        "--end",
        type=str,
        default="now",
        help="The last datetime (YYYY-MM-DD HH:MM:SS) to get data for.",
    )
    parser.add_argument(
        "-n",
        "--ndays",
        type=int,
        default=14,
        help="The number of days to request data for.",
    )
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
        scoot_forecaster = TrafficForecast(**kwargs)
        scoot_forecaster.update_remote_tables()

    except Exception as error:
        print("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
