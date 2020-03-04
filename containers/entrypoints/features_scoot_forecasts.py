"""
Run feature processing using SCOOT forecasts
"""
import argparse
from cleanair.loggers import initialise_logging
from cleanair.features import ScootForecastFeatures
from cleanair.processors import ScootPerDetectorForecaster, ScootPerRoadForecastMapper


def main():
    """
    Forecast SCOOT and convert forecasts into features
    """
    # Read command line arguments
    parser = argparse.ArgumentParser(description="Forecast SCOOT readings")
    parser.add_argument(
        "-s",
        "--secretfile",
        default="db_secrets.json",
        help="File containing connection secrets, (default: 'db_secrets.json').",
    )
    parser.add_argument(
        "-e",
        "--end",
        type=str,
        default="now",
        help="The last datetime (YYYY-MM-DD HH:MM:SS) to get data for, (default: 'now').",
    )
    parser.add_argument(
        "-n",
        "--ndays",
        type=int,
        default=21,
        help="The number of days from the past to use for predicting, (default: 21).",
    )
    parser.add_argument(
        "-f",
        "--forecasthrs",
        type=int,
        default=72,
        help="The number of hours into the future to predict for, (default: 72).",
    )
    parser.add_argument(
        "-d",
        "--detectors",
        nargs="+",
        default=[],
        help="List of detectors to forecast for, (default: all of them).",
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)

    # Parse and interpret arguments
    args = parser.parse_args()
    if args.ndays < 1:
        raise argparse.ArgumentTypeError("Argument --ndays must be greater than 0")

    # Set some parameters using the parsed arguments
    default_logger = initialise_logging(args.verbose)
    detector_ids = args.detectors if args.detectors else None
    ndays = int(args.forecasthrs / 24)

    # Perform update and notify any exceptions
    try:
        # Fit SCOOT readings using Prophet and forecast `args.forecasthrs` into the future
        scoot_forecaster = ScootPerDetectorForecaster(
            ndays=args.ndays,
            end=args.end,
            forecast_length_hrs=args.forecasthrs,
            detector_ids=detector_ids,
            secretfile=args.secretfile,
        )
        forecast_end_time = scoot_forecaster.forecast_end_time
        scoot_forecaster.update_remote_tables()

        # Construct SCOOT forecasts for each road using:
        # - the most recent SCOOT forecasts (from ScootForecast)
        # - the static association between roads and SCOOT sensors (from ScootRoadMatch)
        scoot_road_forecasts = ScootPerRoadForecastMapper(
            ndays=ndays, end=forecast_end_time, secretfile=args.secretfile
        )
        scoot_road_forecasts.update_remote_tables()

        # Construct SCOOT features from forecasts around each interest point
        scoot_feature_extractor = ScootForecastFeatures(
            ndays=ndays, end=forecast_end_time, secretfile=args.secretfile
        )
        scoot_feature_extractor.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred:", str(error))
        raise


if __name__ == "__main__":
    main()
