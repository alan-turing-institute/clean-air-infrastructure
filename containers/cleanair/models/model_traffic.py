"""Traffic model fitting"""
import datetime
from functools import reduce
import logging
import time
import warnings
from fbprophet import Prophet
import pandas as pd
from sqlalchemy.exc import IntegrityError
from ..databases import DBWriter
from ..databases.tables import ScootDetector, ScootReading, ScootForecast
from ..decorators import SuppressStdoutStderr
from ..loggers import duration, get_logger, green
from ..mixins import DateRangeMixin

# Turn off fbprophet stdout logger
logging.getLogger("fbprophet").setLevel(logging.ERROR)


class TrafficForecast(DateRangeMixin, DBWriter):
    """Traffic forecasting using FB prophet"""

    def __init__(self, **kwargs):
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

    def scoot_readings(self, detector_ids=None):
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
            if detector_ids:
                scoot_road_q = scoot_road_q.filter(
                    ScootReading.detector_id.in_(detector_ids)
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

    def forecasts(self, forecast_length_hrs, detector_ids=None):
        """Forecast all features at each detector for the next `forecast_length_hrs`"""
        # Get SCOOT readings from database
        readings = self.scoot_readings(detector_ids=detector_ids)
        training_data = dict(tuple(readings.groupby(["detector_id"])))

        if readings.shape[0] == 0:
            self.logger.error("Could not load any readings!")
            return pd.DataFrame([])

        # The end of the forecast will happen `forecast_length_hrs` into the future
        forecast_end_time = datetime.datetime.now().replace(
            second=0, microsecond=0, minute=0
        ) + datetime.timedelta(hours=forecast_length_hrs)
        self.logger.info(
            "Forecasting SCOOT traffic data up until %s...", forecast_end_time
        )

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
                        start=last_reading_time, end=forecast_end_time, freq="H"
                    )[1:]
                }
            )

            # Iterate over each feature and obtain the forecast for it
            for feature in self.features:
                # Set the maximum value for the fit - this requires the use of logistic
                # regression in the fit itself
                capacity = (
                    100 if "percentage" in feature else 10 * max(fit_data[feature])
                )
                # Construct the prophet model using the fit data
                prophet_data = fit_data.rename(
                    columns={"measurement_start_utc": "ds", feature: "y"}
                )
                prophet_data["cap"] = capacity
                try:
                    with SuppressStdoutStderr():
                        model = Prophet(growth="logistic").fit(prophet_data)
                    # Predict past and future readings for this feature
                    time_range["cap"] = capacity
                    forecast = model.predict(time_range)[["ds", "yhat"]]
                except (ValueError, RuntimeError):
                    self.logger.error(
                        "Prophet prediction failed at '%s' for %s. Using zero instead.",
                        detector_id,
                        feature,
                    )
                    forecast = time_range.copy()
                    forecast["yhat"] = 0

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
            self.logger.info(
                "Finished forecasting detector %s (%i/%i) after %s",
                detector_id,
                idx,
                len(training_data),
                green(duration(start_time, time.time())),
            )
            yield combined_predictions

    def update_remote_tables(self, detector_ids=None):
        """Update the database with new Scoot traffic forecasts."""
        self.logger.info("Starting %s forecasts update...", green("SCOOT"))
        start_time = time.time()
        n_records = 0

        # Get the forecasts and convert to a list of dictionaries
        for forecast_df in self.forecasts(forecast_length_hrs=72, detector_ids=detector_ids):
            forecast_records = forecast_df.to_dict("records")
            if len(forecast_records) > 0:
                self.logger.info(
                    "Preparing to insert %s forecasts into database",
                    green(len(forecast_records)),
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
