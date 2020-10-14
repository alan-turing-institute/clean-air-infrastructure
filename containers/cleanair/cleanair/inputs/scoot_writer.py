"""
Retrieve and process data from the SCOOT traffic detector network
"""
from typing import List, Optional
import datetime
import os
import time
from dateutil import rrule
from dateutil.parser import isoparse
import boto3
import botocore
import pandas
import pytz
from sqlalchemy import func, Table, text, and_, cast, Integer, Float
from ..databases import DBWriter, DBReader
from ..databases.tables import ScootReading
from ..decorators import db_query
from ..loggers import get_logger, green, duration, duration_from_seconds
from ..mixins import DateRangeMixin, ScootQueryMixin
from ..timestamps import datetime_from_unix, unix_from_str, utcstr_from_datetime


ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")


class ScootReader(DateRangeMixin, ScootQueryMixin, DBReader):
    def __init__(self, detector_ids=None, **kwargs):

        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.detector_ids = detector_ids

    @db_query()
    def gen_date_range(self, start_date: str, end_date: Optional[str] = None):
        "Generate a data range and cross join with species"
        with self.dbcnxn.open_session() as session:

            # Generate expected time series
            if end_date:
                reference_end_date_minus_1h = (
                    isoparse(end_date) - datetime.timedelta(hours=1)
                ).isoformat()

                expected_date_times = session.query(
                    func.generate_series(
                        start_date, reference_end_date_minus_1h, ONE_HOUR_INTERVAL,
                    ).label("measurement_start_utc")
                )
            else:
                expected_date_times = session.query(
                    func.generate_series(
                        start_date,
                        func.current_date() - ONE_HOUR_INTERVAL,
                        ONE_HOUR_INTERVAL,
                    ).label("measurement_start_utc")
                )

            return expected_date_times

    @db_query()
    def gen_expected_readings(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        detector_ids: Optional[List[str]] = None,
    ):
        """Generate expected scoot readings between start_date and end_date"""

        detectors_sq = self.scoot_detectors(
            detectors=detector_ids, output_type="subquery"
        )
        daterange_sq = self.gen_date_range(start_date, end_date, output_type="subquery")

        with self.dbcnxn.open_session() as session:

            output = session.query(detectors_sq, daterange_sq)

        if detector_ids:
            return output.filter(detectors_sq.c.detector_id.in_(detector_ids))
        return output

    @db_query()
    def get_reading_status(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        detector_ids: Optional[List[str]] = None,
        only_missing: bool = True,
    ):

        expected_readings = self.gen_expected_readings(
            start_date, end_date, detector_ids, output_type="subquery"
        )

        actual_readings = self.scoot_readings(
            start=start_date,
            upto=end_date,
            detectors=detector_ids,
            output_type="subquery",
        )

        with self.dbcnxn.open_session() as session:

            output = session.query(
                expected_readings.c.detector_id,
                expected_readings.c.measurement_start_utc,
                actual_readings.c.measurement_start_utc.is_(None).label("missing"),
            ).join(
                actual_readings,
                and_(
                    expected_readings.c.detector_id == actual_readings.c.detector_id,
                    expected_readings.c.measurement_start_utc
                    == actual_readings.c.measurement_start_utc,
                ),
                isouter=True,
            )

            if only_missing:
                return output.filter(actual_readings.c.measurement_start_utc.is_(None))

            return output

    @db_query()
    def get_percentage_readings_by_sensor(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        detector_ids: Optional[List[str]] = None,
        group_daily: bool = False,
    ):

        reading_status_sq = self.get_reading_status(
            start_date,
            end_date,
            detector_ids,
            only_missing=False,
            output_type="subquery",
        )

        with self.dbcnxn.open_session() as session:

            if group_daily:

                return (
                    session.query(
                        reading_status_sq.c.detector_id,
                        func.date_trunc(
                            "day", reading_status_sq.c.measurement_start_utc
                        ).label("day"),
                        (
                            cast(
                                func.sum(
                                    cast(
                                        (reading_status_sq.c.missing == False), Integer,
                                    )
                                ),
                                Float,
                            )
                            / cast(func.count(reading_status_sq.c.missing), Float)
                        ).label("percent_complete"),
                    )
                    .group_by(
                        reading_status_sq.c.detector_id,
                        func.date_trunc(
                            "day", reading_status_sq.c.measurement_start_utc
                        ),
                    )
                    .order_by(
                        reading_status_sq.c.detector_id,
                        func.date_trunc(
                            "day", reading_status_sq.c.measurement_start_utc
                        ),
                    )
                )

            return session.query(
                reading_status_sq.c.detector_id,
                (
                    cast(
                        func.sum(cast(reading_status_sq.c.missing == False, Integer)),
                        Float,
                    )
                    / cast(func.count(reading_status_sq.c.missing), Float)
                ).label("percent_complete"),
            ).group_by(reading_status_sq.c.detector_id)

    @db_query()
    def get_percentage_readings_quantiles(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        detector_ids: Optional[List[str]] = None,
    ):

        percentage_by_sensor_day_sq = self.get_percentage_readings_by_sensor(
            start_date,
            end_date,
            group_daily=True,
            detector_ids=detector_ids,
            output_type="subquery",
        )

        def cum_quant(lower, upper):
            "Calculate the percentage in (lower, upper] and label the column [upper]"
            return (
                cast(
                    func.sum(
                        cast(
                            and_(
                                percentage_by_sensor_day_sq.c.percent_complete > lower,
                                percentage_by_sensor_day_sq.c.percent_complete <= upper,
                            ),
                            Integer,
                        )
                    ),
                    Float,
                )
                / cast(
                    func.count(percentage_by_sensor_day_sq.c.percent_complete), Float
                )
                * 100
            ).label(f"{upper}")

        with self.dbcnxn.open_session() as session:

            return (
                session.query(
                    percentage_by_sensor_day_sq.c.day,
                    cum_quant(-1, 0.0),
                    cum_quant(0.0, 0.25),
                    cum_quant(0.25, 0.5),
                    cum_quant(0.5, 0.75),
                    cum_quant(0.75, 0.9),
                    cum_quant(0.9, 1),
                    func.count(percentage_by_sensor_day_sq.c.percent_complete).label(
                        "n_sensors"
                    ),
                )
                .group_by(percentage_by_sensor_day_sq.c.day)
                .order_by(percentage_by_sensor_day_sq.c.day)
            )


class ScootWriter(DateRangeMixin, DBWriter):
    """
    Class to get data from the SCOOT traffic detector network via the S3 bucket maintained by TfL:
    (https://s3.console.aws.amazon.com/s3/buckets/surface.data.tfl.gov.uk)
    """

    def __init__(self, aws_key_id, aws_key, detector_ids=None, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.detector_ids = detector_ids

        # Set up AWS access keys
        self.access_key_id = aws_key_id
        self.access_key = aws_key

        # Set up the known column names
        self.csv_columns = [
            "timestamp",
            "detector_id",
            "detector_fault",
            "n_vehicles_in_interval",
            "occupancy_percentage",
            "congestion_percentage",
            "saturation_percentage",
            "flow_raw_count",
            "occupancy_raw_count",
            "congestion_raw_count",
            "saturation_raw_count",
            "region",
        ]

    def request_site_entries(self):
        """Get list of known detectors"""
        with self.dbcnxn.open_session() as session:
            scoot_detector = Table(
                "scoot_detector",
                ScootReading.metadata,
                schema="interest_points",
                autoload=True,
                autoload_with=self.dbcnxn.engine,
            )
            detectors = sorted(
                [s[0] for s in session.query(scoot_detector.c.detector_n).distinct()]
            )
        return detectors

    @db_query()
    def get_existing_scoot_data(self):
        """Get all the SCOOT readings already in the database for the given time range and set of detector IDs"""
        with self.dbcnxn.open_session() as session:
            q_scoot_readings = (
                session.query(
                    func.date_trunc("hour", ScootReading.measurement_start_utc).label(
                        "hour"
                    ),
                    ScootReading.detector_id,
                    func.count(ScootReading.measurement_start_utc).label("n_entries"),
                )
                .group_by(
                    ScootReading.detector_id,
                    func.date_trunc("hour", ScootReading.measurement_start_utc),
                )
                .filter(
                    ScootReading.measurement_start_utc >= self.start_datetime,
                    ScootReading.measurement_start_utc <= self.end_datetime,
                )
            )
        return q_scoot_readings

    @staticmethod
    def get_remote_filenames(start_datetime_utc, end_datetime_utc):
        """Get all possible remote file details for the period in question"""

        # Convert datetime from UTC to local time
        start_datetime = start_datetime_utc.replace(
            tzinfo=datetime.timezone.utc
        ).astimezone(tz=pytz.timezone("Europe/London"))
        end_datetime = end_datetime_utc.replace(
            tzinfo=datetime.timezone.utc
        ).astimezone(tz=pytz.timezone("Europe/London"))

        # List all the relevant CSV files for the time range under consideration
        file_list = []
        for date in rrule.rrule(
            rrule.HOURLY, dtstart=start_datetime, until=end_datetime
        ):
            # NB. We must explicitly exclude end_datetime
            if date >= end_datetime:
                continue
            year, month, day, hour = (
                str(date.year),
                str(date.month).zfill(2),
                str(date.day).zfill(2),
                str(date.hour).zfill(2),
            )
            for timestring in [hour + str(m).zfill(2) for m in range(60)]:
                csv_name = "{y}{m}{d}-{timestring}.csv".format(
                    y=year, m=month, d=day, timestring=timestring
                )
                file_list.append(
                    (
                        "Control/TIMSScoot/{y}/{m}/{d}".format(y=year, m=month, d=day),
                        csv_name,
                    )
                )
        return file_list

    def request_remote_data(self, start_datetime_utc, end_datetime_utc, detector_ids):
        """
        Request all readings between {start_date} and {end_date}.
        Remove readings with unknown detector ID or detector faults.
        """
        start_aws = time.time()

        # Get an AWS client
        client = boto3.client(
            "s3",
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.access_key,
        )

        # Parse each CSV file into a dataframe and add these to a list
        n_failed, n_succeeded = 0, 0
        processed_readings = []
        for filepath, filename in self.get_remote_filenames(
            start_datetime_utc, end_datetime_utc
        ):
            try:
                self.logger.debug("Requesting scoot file %s", filename)
                client.download_file(
                    "surface.data.tfl.gov.uk",
                    "{path}/{file}".format(path=filepath, file=filename),
                    filename,
                )
                # Read the CSV files into a dataframe
                scoot_df = pandas.read_csv(
                    filename,
                    names=self.csv_columns,
                    skipinitialspace=True,
                    converters={
                        "timestamp": lambda x: unix_from_str(
                            x, timezone="Europe/London"
                        ),
                        "n_vehicles_in_interval": lambda x: float(x) / 60,
                        "detector_fault": lambda x: x.strip() == "Y",
                        "region": lambda x: x.strip(),
                    },
                )
                # Remove any sites that we do not currently plan to process
                scoot_df = scoot_df[scoot_df["detector_id"].isin(detector_ids)]
                # Remove any readings with detector faults
                scoot_df = scoot_df[~scoot_df["detector_fault"]]
                # Append to list of readings
                processed_readings.append(scoot_df)
                n_succeeded += 1
            except (
                botocore.exceptions.ClientError,
                botocore.exceptions.EndpointConnectionError,
            ) as error:
                self.logger.error("Failed to retrieve %s. Error: %s", filename, error)
                n_failed += 1
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                self.logger.debug("Loaded readings from %s", green(filename))

        # Log success/failure
        if n_failed > 3:
            raise Exception(
                "{} expected files could not be downloaded".format(n_failed)
            )
        self.logger.info(
            "Successfully retrieved %s SCOOT files", green(f"{n_succeeded}/60")
        )

        # Combine the readings into a single data frame
        df_combined = pandas.concat(processed_readings, ignore_index=True)
        self.logger.info(
            "Filtered %s relevant per-minute detector readings in %s",
            green(df_combined.shape[0]),
            green(duration(start_aws, time.time())),
        )
        return df_combined

    def combine_by_detector_id(self, input_df):
        """Aggregate measurements by detector ID across several readings"""
        # Group by detector_id: each column has its own combination rule
        try:
            # Scale all summed variables to correct for possible missing values from detector faults
            return input_df.groupby(["detector_id"]).agg(
                {
                    "detector_id": "first",
                    "n_vehicles_in_interval": lambda x: sum(x) * (60.0 / len(x)),
                    "occupancy_percentage": "mean",
                    "congestion_percentage": "mean",
                    "saturation_percentage": "mean",
                    "flow_raw_count": lambda x: sum(x) * (60.0 / len(x)),
                    "occupancy_raw_count": lambda x: sum(x) * (60.0 / len(x)),
                    "congestion_raw_count": lambda x: sum(x) * (60.0 / len(x)),
                    "saturation_raw_count": lambda x: sum(x) * (60.0 / len(x)),
                    "region": "first",
                }
            )
        except pandas.core.base.DataError:
            self.logger.warning(
                "Data aggregation failed - returning an empty dataframe"
            )
            return pandas.DataFrame(columns=input_df.columns)

    def aggregate_scoot_data(self, df_readings):
        """
        Aggregate scoot data by detector ID into hourly chunks
        """
        # Get the minimum and maximum time in the dataset
        try:
            time_min = datetime_from_unix(df_readings["timestamp"].min())
            time_max = datetime_from_unix(df_readings["timestamp"].max())
        except ValueError:
            return

        # Slice processed data into hourly chunks and aggregate these by detector ID
        for start_time in rrule.rrule(
            rrule.HOURLY,
            dtstart=time_min.replace(minute=0, second=0, microsecond=0),
            until=time_max,
        ):
            end_time = start_time + datetime.timedelta(hours=1)

            # Construct hourly data
            self.logger.info(
                "Processing data from %s to %s", green(start_time), green(end_time)
            )
            df_hourly = df_readings.loc[
                (df_readings["timestamp"] > start_time.timestamp())
                & (df_readings["timestamp"] <= end_time.timestamp())
            ].copy()

            # Drop unused columns and aggregate
            self.logger.info(
                "Aggregating %s readings by site", green(df_hourly.shape[0])
            )
            df_hourly.drop(["detector_fault", "timestamp"], axis=1, inplace=True)
            df_aggregated = self.combine_by_detector_id(df_hourly)

            # Add timestamps
            df_aggregated["measurement_start_utc"] = utcstr_from_datetime(start_time)
            df_aggregated["measurement_end_utc"] = utcstr_from_datetime(end_time)

            yield df_aggregated

    def update_remote_tables(self):
        """Update the database with new SCOOT traffic data."""
        self.logger.info(
            "Retrieving new %s readings from %s to %s...",
            green("SCOOT"),
            green(self.start_datetime),
            green(self.end_datetime),
        )
        start_update = time.time()
        n_records_inserted = 0

        # Use all known detectors if no list is provided
        if not self.detector_ids:
            self.detector_ids = self.request_site_entries()
        self.logger.info(
            "Requesting readings from %s for %s detector(s)",
            green("TfL AWS S3 storage"),
            green(len(self.detector_ids)),
        )

        # Processing will take approximately one second for each minute of data to process
        self.logger.info(
            "Processing will take approximately %s...",
            green(
                duration_from_seconds(
                    (self.end_datetime - self.start_datetime).total_seconds() / 60.0
                )
            ),
        )

        # Get a per-hour summary of records in this range that are already in the database
        db_records = self.get_existing_scoot_data(output_type="df")

        # Process one hour at a time
        start_hour = self.start_datetime.replace(microsecond=0, second=0, minute=0)
        for start_datetime_utc in rrule.rrule(
            rrule.HOURLY, dtstart=start_hour, until=self.end_datetime
        ):
            end_datetime_utc = start_datetime_utc + datetime.timedelta(hours=1)

            # Filter out any detectors that have already been processed
            processed_detectors = db_records[db_records["hour"] == start_datetime_utc][
                "detector_id"
            ].tolist()
            unprocessed_detectors = [
                d for d in self.detector_ids if d not in processed_detectors
            ]
            if unprocessed_detectors:
                self.logger.info(
                    "Processing S3 data from %s to %s for %s detector(s).",
                    green(start_datetime_utc),
                    green(end_datetime_utc),
                    green(len(unprocessed_detectors)),
                )
            else:
                # If all detectors have been processed then skip this hour
                self.logger.info(
                    "No S3 data is needed from %s to %s. %s detector(s) have already been processed.",
                    green(start_datetime_utc),
                    green(end_datetime_utc),
                    green(len(processed_detectors)),
                )
                continue

            # Load all valid remote data into a single dataframe
            df_readings = self.request_remote_data(
                start_datetime_utc, end_datetime_utc, unprocessed_detectors
            )

            if df_readings.shape[0] < 1:
                self.logger.warning(
                    "Skipping hour %s to %s as it has no unprocessed data",
                    green(start_datetime_utc),
                    green(end_datetime_utc),
                )
                continue

            # Aggregate the data and add readings to database
            for df_aggregated in self.aggregate_scoot_data(df_readings):
                site_records = df_aggregated.to_dict("records")
                self.logger.info(
                    "Inserting records for %s detectors into database",
                    green(len(site_records)),
                )

                start_session = time.time()

                # Commit the records to the database
                self.commit_records(
                    site_records, on_conflict="overwrite", table=ScootReading,
                )
                n_records_inserted += len(site_records)

                self.logger.info(
                    "Insertion took %s", green(duration(start_session, time.time())),
                )

        # Summarise updates
        self.logger.info(
            "Committed %s records to table %s in %s",
            green(n_records_inserted),
            green(ScootReading.__tablename__),
            green(duration(start_update, time.time())),
        )
