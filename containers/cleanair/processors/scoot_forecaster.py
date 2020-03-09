"""Traffic model fitting"""
import datetime
from functools import partial, reduce
import logging
import time
from pathos.multiprocessing import ProcessingPool as Pool
from fbprophet import Prophet
import pandas as pd
from sqlalchemy.exc import IntegrityError
from ..databases import DBWriter
from ..databases.tables import ScootReading, ScootForecast
from ..decorators import SuppressStdoutStderr
from ..loggers import duration, duration_from_seconds, get_logger, green
from ..mixins import DateRangeMixin

# Turn off fbprophet stdout logger
logging.getLogger("fbprophet").setLevel(logging.ERROR)


class ScootPerDetectorForecaster(DateRangeMixin, DBWriter):
    """Traffic forecasting using FB prophet"""

    def __init__(self, forecast_length_hrs=72, detector_ids=None, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        self.features = [
            "n_vehicles_in_interval",
            "occupancy_percentage",
            "congestion_percentage",
            "saturation_percentage",
        ]

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.detector_ids = detector_ids
        self.forecast_length_hrs = forecast_length_hrs

        # The end of the forecast will happen `self.forecast_length_hrs` into the future
        self.forecast_end_time = datetime.datetime.now().replace(
            second=0, microsecond=0, minute=0
        ) + datetime.timedelta(hours=self.forecast_length_hrs)

    def scoot_readings(self):
        """Get SCOOT readings between start and end times"""
        self.logger.info(
            "Requesting SCOOT readings between %s and %s",
            self.start_datetime,
            self.end_datetime,
        )
        start_time = time.time()

        with self.dbcnxn.open_session() as session:
            q_scoot_reading = session.query(ScootReading).filter(
                ScootReading.measurement_start_utc >= self.start_datetime,
                ScootReading.measurement_start_utc < self.end_datetime,
            )
            if self.detector_ids:
                q_scoot_reading = q_scoot_reading.filter(
                    ScootReading.detector_id.in_(self.detector_ids)
                )
            q_scoot_reading = q_scoot_reading.order_by(
                ScootReading.detector_id, ScootReading.measurement_start_utc
            )
        df_scoot_readings = pd.read_sql(
            q_scoot_reading.statement, q_scoot_reading.session.bind
        )
        self.logger.info(
            "Retrieved %s SCOOT readings in %s minutes",
            green(len(df_scoot_readings)),
            green(duration(start_time, time.time())),
        )
        return df_scoot_readings

    def forecasts(self, pool_size=10):
        """Forecast all features at each detector up until `self.forecast_end_time`"""
        # Get all SCOOT readings within the relevant time period from the database and
        # group them by detector ID
        df_scoot_readings = self.scoot_readings()
        df_per_detector = df_scoot_readings.groupby(["detector_id"])

        n_detectors = len(df_per_detector)
        if not n_detectors:
            self.logger.error("Could not load any readings!")
            return pd.DataFrame([])

        # Processing will take approximately three seconds per detector being processed
        self.logger.info(
            "Forecasting up until %s will take approximately %s...",
            self.forecast_end_time,
            duration_from_seconds(3 * n_detectors),
        )

        # Obtain the forecast for all features at a single detector
        def forecast_one_detector(input_data, logger, features, forecast_end_time):
            # Construct the time range to predict over. This is functionally identical
            # to `make_future_dataframe` but works even in cases where there is
            # insufficient data for Prophet to run.
            detector_id, detector_data = input_data
            last_reading_time = max(detector_data["measurement_start_utc"])
            time_range = pd.DataFrame(
                {
                    "ds": pd.date_range(
                        start=last_reading_time, end=forecast_end_time, freq="H"
                    )[1:]
                }
            )

            # Obtain the forecast for each feature
            feature_predictions = []
            for feature in features:
                # Construct the prophet model using a copy of the fit data
                prophet_data = detector_data.rename(
                    columns={"measurement_start_utc": "ds", feature: "y"}
                )
                # Set the maximum value for the fit - this requires the use of logistic
                # regression in the fit itself
                capacity = (
                    100 if "percentage" in feature else 10 * max(detector_data[feature])
                )
                prophet_data["cap"] = capacity
                try:
                    # Fit model and predict future readings for this feature
                    # while suppressing Stan and numpy warnings
                    with SuppressStdoutStderr():
                        model = Prophet(growth="logistic").fit(prophet_data)
                        # Make a copy with a 'cap' column included
                        capped_time_range = time_range.assign(cap=capacity)
                        forecast = model.predict(capped_time_range)[["ds", "yhat"]]
                except (ValueError, RuntimeError):
                    logger.error(
                        "Prophet prediction failed at '%s' for %s. Using zero instead.",
                        detector_id,
                        feature,
                    )
                    # Make a copy with a 'yhat' column included
                    forecast = time_range.assign(yhat=0)

                # Rename the columns
                forecast.rename(
                    columns={"ds": "measurement_start_utc", "yhat": feature},
                    inplace=True,
                )
                # Keep only future predictions and force all predictions to be positive
                forecast = forecast[
                    forecast["measurement_start_utc"] > last_reading_time
                ]
                forecast[feature].clip(lower=0, inplace=True)
                feature_predictions.append(forecast)

            # Combine predicted features and add detector ID
            combined_predictions = reduce(
                lambda df1, df2: df1.merge(df2, on="measurement_start_utc"),
                feature_predictions,
            )
            combined_predictions["detector_id"] = detector_id
            combined_predictions["measurement_end_utc"] = combined_predictions[
                "measurement_start_utc"
            ] + datetime.timedelta(hours=1)
            return (detector_id, combined_predictions)

        # Setup a pool to allow us to process multiple detectors in parallel
        processing_pool = Pool(pool_size)

        # Initialise counters
        detector_idx = 0
        start_time = time.time()

        # Bind instance parameters to produce function without external variables
        bound_forecast = partial(
            forecast_one_detector,
            logger=self.logger,
            features=self.features,
            forecast_end_time=self.forecast_end_time,
        )

        # Iterate over each detector ID and obtain the forecast for it
        # for result in processing_pool.uimap(bound_forecast, training_data.items()):
        for result in processing_pool.uimap(bound_forecast, df_per_detector):
            # Log some statistics then yield this forecast
            detector_idx += 1
            elapsed_seconds = time.time() - start_time
            remaining_seconds = elapsed_seconds * (n_detectors / detector_idx - 1)
            self.logger.info(
                "Finished forecasting detector %s (%i/%i) after %s. Remaining: %s.",
                result[0],
                detector_idx,
                n_detectors,
                green(duration_from_seconds(elapsed_seconds)),
                green(duration_from_seconds(remaining_seconds)),
            )
            yield result

    def update_remote_tables(self):
        """Update the database with new Scoot traffic forecasts."""
        self.logger.info(
            "Preparing to forecast SCOOT up until %s", self.forecast_end_time
        )
        start_time = time.time()
        n_records = 0

        # Get the forecasts and convert to a list of dictionaries
        for detector_id, forecast_df in self.forecasts():
            forecast_records = forecast_df.to_dict("records")
            if len(forecast_records) > 0:
                self.logger.info(
                    "Preparing to insert %s hourly forecasts for %s into ScootForecast table",
                    green(len(forecast_records)),
                    detector_id,
                )

                # Add forecasts to the database
                with self.dbcnxn.open_session() as session:
                    try:
                        # Commit and override any existing forecasts
                        self.commit_records(
                            session,
                            forecast_records,
                            on_conflict="overwrite",
                            table=ScootForecast,
                        )
                        n_records += len(forecast_records)
                    except IntegrityError as error:
                        self.logger.error(
                            "Failed to add forecasts to the database: %s", type(error)
                        )
                        self.logger.error(str(error))
                        session.rollback()

        # Summarise updates
        self.logger.info(
            "Committed %s forecasts to table %s in %s",
            green(n_records),
            green(ScootForecast.__tablename__),
            green(duration(start_time, time.time())),
        )
