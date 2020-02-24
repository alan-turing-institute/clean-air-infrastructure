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
from ..loggers import duration, get_logger, green
from ..mixins import DateRangeMixin

# Turn off fbprophet stdout logger
logging.getLogger("fbprophet").setLevel(logging.ERROR)


class TrafficForecast(DateRangeMixin, DBWriter):
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
            scoot_road_q = session.query(ScootReading).filter(
                ScootReading.measurement_start_utc >= self.start_datetime,
                ScootReading.measurement_start_utc < self.end_datetime,
            )
            if self.detector_ids:
                scoot_road_q = scoot_road_q.filter(
                    ScootReading.detector_id.in_(self.detector_ids)
                )
            scoot_road_q = scoot_road_q.order_by(
                ScootReading.detector_id, ScootReading.measurement_start_utc
            )
        readings = pd.read_sql(scoot_road_q.statement, scoot_road_q.session.bind)
        self.logger.info(
            "Retrieved %s SCOOT readings in %s minutes",
            green(len(readings)),
            green("{:.2f}".format((time.time() - start_time) / 60.0)),
        )
        return readings

    def forecasts(self):
        """Forecast all features at each detector up until `self.forecast_end_time`"""
        # Get all SCOOT readings within the relevant time period from database and group them by detector ID
        readings = self.scoot_readings()
        training_data = dict(tuple(readings.groupby(["detector_id"])))

        if not readings.shape[0]:
            self.logger.error("Could not load any readings!")
            return pd.DataFrame([])

        self.logger.info(
            "Forecasting SCOOT traffic data up until %s...", self.forecast_end_time
        )

        # Setup a pool to allow us to process all features in parallel
        processing_pool = Pool(len(self.features))

        # Iterate over each detector ID and obtain the forecast for it
        for idx, (detector_id, fit_data) in enumerate(training_data.items(), start=1):
            start_time = time.time()
            feature_predictions = []

            # Construct the time range to predict over. This is functionally identical
            # to `make_future_dataframe` but works even in cases where there is
            # insufficient data for Prophet to run.
            last_reading_time = max(fit_data["measurement_start_utc"])
            time_range = pd.DataFrame(
                {
                    "ds": pd.date_range(
                        start=last_reading_time, end=self.forecast_end_time, freq="H"
                    )[1:]
                }
            )

            # Obtain the forecast for a single feature
            def forecast_one_feature(
                feature,
                _logger,
                _fit_data,
                _time_range,
                _last_reading_time,
                _detector_id,
            ):
                # Set the maximum value for the fit - this requires the use of logistic
                # regression in the fit itself
                capacity = (
                    100 if "percentage" in feature else 10 * max(_fit_data[feature])
                )
                # Construct the prophet model using a copy of the fit data
                prophet_data = _fit_data.rename(
                    columns={"measurement_start_utc": "ds", feature: "y"}
                )
                prophet_data["cap"] = capacity
                try:
                    # Fit model while suppressing Stan output lines
                    with SuppressStdoutStderr():
                        model = Prophet(growth="logistic").fit(prophet_data)
                    # Predict past and future readings for this feature
                    _time_range["cap"] = capacity
                    forecast = model.predict(_time_range)[["ds", "yhat"]]
                except (ValueError, RuntimeError):
                    _logger.error(
                        "Prophet prediction failed at '%s' for %s. Using zero instead.",
                        _detector_id,
                        feature,
                    )
                    forecast = _time_range.copy()
                    forecast["yhat"] = 0

                # Rename the columns
                forecast.rename(
                    columns={"ds": "measurement_start_utc", "yhat": feature},
                    inplace=True,
                )
                # Keep only future predictions and force all predictions to be positive
                forecast = forecast[
                    forecast["measurement_start_utc"] > _last_reading_time
                ]
                forecast[feature].clip(lower=0, inplace=True)
                # feature_predictions.append(forecast)
                return forecast

            bound_forecast = partial(
                forecast_one_feature,
                _logger=self.logger,
                _fit_data=fit_data,
                _time_range=time_range,
                _last_reading_time=last_reading_time,
                _detector_id=detector_id,
            )
            feature_predictions = processing_pool.map(bound_forecast, self.features)

            # Combine predicted features and add detector ID
            combined_predictions = reduce(
                lambda df1, df2: df1.merge(df2, on="measurement_start_utc"),
                feature_predictions,
            )
            combined_predictions["detector_id"] = detector_id
            combined_predictions["measurement_end_utc"] = combined_predictions[
                "measurement_start_utc"
            ] + datetime.timedelta(hours=1)
            self.logger.info(
                "Finished forecasting detector %s (%i/%i) after %s",
                detector_id,
                idx,
                len(training_data),
                green(duration(start_time, time.time())),
            )
            yield (detector_id, combined_predictions)

    def update_remote_tables(self):
        """Update the database with new Scoot traffic forecasts."""
        self.logger.info("Starting %s forecasts update...", green("SCOOT"))
        start_time = time.time()
        n_records = 0

        # Get the forecasts and convert to a list of dictionaries
        for detector_id, forecast_df in self.forecasts():
            forecast_records = forecast_df.to_dict("records")
            if len(forecast_records) > 0:
                self.logger.info(
                    "Preparing to insert %s hourly forecasts for %s into database",
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
