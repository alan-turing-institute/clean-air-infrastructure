# """
# Run feature processing using SCOOT forecasts
# """
# from cleanair.loggers import initialise_logging
# from cleanair.features import ScootForecastFeatures
# from cleanair.processors import ScootPerDetectorForecaster, ScootPerRoadForecastMapper
# from cleanair.parsers import ScootForecastFeatureArgumentParser


# def main():
#     """
#     Forecast SCOOT and convert forecasts into features
#     """
#     # Parse and interpret command line arguments
#     args = ScootForecastFeatureArgumentParser(
#         description="Forecast SCOOT and extract model features",
#         nhours=336,  # this is two weeks
#         sources=["satellite", "hexgrid"],
#     ).parse_args()

#     # Set some parameters using the parsed arguments
#     default_logger = initialise_logging(args.verbose)
#     detector_ids = args.detectors if args.detectors else None

#     # Update SCOOT forecasts and features on the database, logging any unhandled exceptions
#     try:
#         # Fit SCOOT readings using Prophet and forecast `args.forecasthrs` into the future
#         scoot_forecaster = ScootPerDetectorForecaster(
#             nhours=args.nhours,
#             end=args.upto,
#             forecast_length_hrs=args.forecasthrs,
#             detector_ids=detector_ids,
#             secretfile=args.secretfile,
#         )
#         forecast_end_time = scoot_forecaster.forecast_end_time
#         scoot_forecaster.update_remote_tables()

#         # Construct SCOOT forecasts for each road using:
#         # - the most recent SCOOT forecasts (from ScootForecast)
#         # - the static association between roads and SCOOT sensors (from ScootRoadMatch)
#         scoot_road_forecasts = ScootPerRoadForecastMapper(
#             nhours=args.forecasthrs, end=forecast_end_time, secretfile=args.secretfile
#         )
#         scoot_road_forecasts.update_remote_tables()

#         # Construct SCOOT features from forecasts around each interest point
#         scoot_feature_extractor = ScootForecastFeatures(
#             nhours=args.forecasthrs,
#             end=forecast_end_time,
#             secretfile=args.secretfile,
#             sources=args.sources,
#         )
#         scoot_feature_extractor.update_remote_tables()

#     except Exception as error:
#         default_logger.error("An uncaught exception occurred: %s", str(error))
#         raise


# if __name__ == "__main__":
#     main()
