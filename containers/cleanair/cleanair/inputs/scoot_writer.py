"""
Retrieve and process data from the SCOOT traffic detector network
"""

from typing import List, Tuple, Any, Optional
import datetime
from datetime import timedelta
import os
import time
from dateutil import rrule
import boto3
import botocore
import pandas as pd
import pytz
from sqlalchemy import Table
from ..databases import DBWriter
from ..databases.tables import ScootReading
from ..decorators import db_query
from ..loggers import get_logger, green, duration, duration_from_seconds
from ..mixins import DateRangeMixin, ScootQueryMixin
from ..timestamps import unix_from_str, utcstr_from_datetime


class ScootWriter(DateRangeMixin, DBWriter, ScootQueryMixin):
    """
    Class to get data from the SCOOT traffic detector network via the S3 bucket maintained by TfL:
    (https://s3.console.aws.amazon.com/s3/buckets/surface.data.tfl.gov.uk)
    """

    def __init__(
        self,
        aws_key_id: str,
        aws_key: str,
        detector_ids: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # If detector_ids not provided get from database
        self.detector_ids = (
            detector_ids if detector_ids else self.request_site_entries()
        )

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

    def request_site_entries(self) -> List[str]:
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
    def __check_detectors_processed(
        self, measurement_start_utc: datetime.datetime,
    ) -> Any:
        "Return detector ids which are in the database at a given hour"

        with self.dbcnxn.open_session() as session:

            detector_ids = session.query(ScootReading.detector_id).filter(
                ScootReading.measurement_start_utc == measurement_start_utc.isoformat(),
            )

            return detector_ids

    def check_detectors_processed(
        self, measurement_start_utc: datetime.datetime, detector_ids: List[str]
    ) -> bool:
        "Check if a lit of detector_ids exist in the database for a given hour"
        all_processed_set = set(
            self.__check_detectors_processed(measurement_start_utc, output_type="list")
        )

        return set(detector_ids) == all_processed_set

    @staticmethod
    def get_remote_filenames(
        start_datetime_utc: datetime.datetime,
    ) -> List[Tuple[str, str]]:
        """Get all possible remote file details for the hour starting at start_datetime_utc"""

        # Convert datetime from UTC to local time
        start_datetime = start_datetime_utc.replace(
            tzinfo=datetime.timezone.utc
        ).astimezone(tz=pytz.timezone("Europe/London"))

        # List all the relevant CSV files for the time range under consideration
        file_list = []
        year, month, day, hour = (
            str(start_datetime.year),
            str(start_datetime.month).zfill(2),
            str(start_datetime.day).zfill(2),
            str(start_datetime.hour).zfill(2),
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

    def request_remote_data(
        self, start_datetime_utc: datetime.datetime, detector_ids: List[str],
    ) -> pd.DataFrame:
        """
        Request all readings for the hour starting at start_datetime_utc
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
        for filepath, filename in self.get_remote_filenames(start_datetime_utc):
            try:
                self.logger.debug("Requesting scoot file %s", filename)
                client.download_file(
                    "surface.data.tfl.gov.uk",
                    "{path}/{file}".format(path=filepath, file=filename),
                    filename,
                )
                # Read the CSV files into a dataframe
                scoot_df = pd.read_csv(
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
        df_combined = pd.concat(processed_readings, ignore_index=True)
        self.logger.info(
            "Filtered %s relevant per-minute detector readings in %s",
            green(df_combined.shape[0]),
            green(duration(start_aws, time.time())),
        )
        return df_combined

    def combine_by_detector_id(self, input_df: pd.DataFrame) -> pd.DataFrame:
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
        except pd.core.base.DataError:
            self.logger.warning(
                "Data aggregation failed - returning an empty dataframe"
            )
            return pd.DataFrame(columns=input_df.columns)

    def aggregate_scoot_data_hour(
        self, df_readings: pd.DataFrame, start_datetime_utc: datetime.datetime
    ) -> pd.DataFrame:
        """
        Aggregate one hour of scoot data by detector ID

        Args:
            df_readings: A dataframe containing one hour of scoot readings.
                If multiple hour are provided will only process the first hour
        """
        # Get the minimum and maximum time in the dataset
        time_min = start_datetime_utc

        # Slice processed data into hourly chunks and aggregate these by detector ID
        start_time = time_min.replace(minute=0, second=0, microsecond=0)
        end_time = start_time + datetime.timedelta(hours=1)

        # Construct hourly data
        self.logger.info(
            "Processing data from %s to %s", green(start_time), green(end_time)
        )
        df_hourly = df_readings.loc[
            (df_readings["timestamp"] >= start_time.timestamp())
            & (df_readings["timestamp"] < end_time.timestamp())
        ].copy()

        # Drop unused columns and aggregate
        self.logger.info("Aggregating %s readings by site", green(df_hourly.shape[0]))
        df_hourly.drop(["detector_fault", "timestamp"], axis=1, inplace=True)
        df_aggregated = self.combine_by_detector_id(df_hourly)

        # Add timestamps
        df_aggregated["measurement_start_utc"] = utcstr_from_datetime(start_time)
        df_aggregated["measurement_end_utc"] = utcstr_from_datetime(end_time)

        return df_aggregated

    def process_hour(self, measurement_start_utc: datetime.datetime) -> None:
        "Request scoot data for a given hour and process it"

        measurement_end_utc = measurement_start_utc + datetime.timedelta(hours=1)

        if self.check_detectors_processed(measurement_start_utc, self.detector_ids):

            self.logger.info(
                "No S3 data is needed from %s. %s detector(s) have already been processed.",
                green(measurement_start_utc),
                green(len(self.detector_ids)),
            )

            return

        self.logger.info(
            "Processing S3 data from %s to %s",
            green(measurement_start_utc),
            green(measurement_end_utc),
        )

        # Load all valid remote data into a single dataframe
        df_readings = self.request_remote_data(measurement_start_utc, self.detector_ids)

        if df_readings.shape[0] < 1:
            self.logger.warning(
                "Skipping hour %s to %s as it has no unprocessed data",
                green(measurement_start_utc),
                green(measurement_end_utc),
            )
            return

        # Aggregate hourly readings scoot readings
        df_aggregated_readings = self.aggregate_scoot_data_hour(
            df_readings, measurement_start_utc
        )

        # Join with expected readings to get nulls where no data was retrived from S3 bucket
        df_joined_with_expected = self.join_with_expected_readings(
            df_aggregated_readings,
            measurement_start_utc,
            measurement_end_utc,
            self.detector_ids,
        )

        site_records = df_joined_with_expected.to_dict("records")

        site_record_drop_null = [
            {
                key: (value if not pd.isna(value) else None)
                for (key, value) in record.items()
            }
            for record in site_records
        ]

        self.logger.info(
            "Inserting records for %s detectors into database",
            green(len(site_record_drop_null)),
        )

        # Commit the records to the database
        start_session = time.time()
        self.commit_records(
            site_record_drop_null, on_conflict="overwrite", table=ScootReading,
        )
        self.logger.info(
            "Insertion took %s", green(duration(start_session, time.time())),
        )

        return

    def join_with_expected_readings(
        self,
        df_aggregated: pd.DataFrame,
        measurement_start_utc: datetime.datetime,
        measurement_end_utc: datetime.datetime,
        detector_ids: List[str],
    ) -> pd.DataFrame:
        "Join a dataframe of scoot aggregated scoot readings with a dataframe of expected detector ids and times" ""

        expected_readings = pd.DataFrame(
            [
                {
                    "detector_id": i,
                    "measurement_start_utc": utcstr_from_datetime(
                        measurement_start_utc.replace(tzinfo=datetime.timezone.utc)
                    ),
                    "measurement_end_utc": utcstr_from_datetime(
                        measurement_end_utc.replace(tzinfo=datetime.timezone.utc)
                    ),
                }
                for i in detector_ids
            ]
        )

        # Left join processed data onto expected data. Missing data will be null
        expected_merged = pd.merge(
            expected_readings,
            df_aggregated.reset_index(drop=True),
            on=["detector_id", "measurement_start_utc", "measurement_end_utc"],
            how="left",
        )

        n_readings = expected_merged.shape[0]
        n_null = pd.isnull(expected_merged["n_vehicles_in_interval"]).sum()

        self.logger.info(
            """Requested data for %s sensors. %s out of %s have data.
            Missing data for %s sensors will insert as null""",
            len(detector_ids),
            n_readings - n_null,
            n_readings,
            n_null,
        )

        return expected_merged

    def update_remote_tables(self) -> None:
        """Update the database with new SCOOT traffic data."""

        self.logger.info(
            "Retrieving new %s readings from %s to %s...",
            green("SCOOT"),
            green(self.start_datetime),
            green(self.end_datetime),
        )
        start_update = time.time()
        n_records_inserted = 0

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

        # Process one hour at a time
        start_hour = self.start_datetime.replace(microsecond=0, second=0, minute=0)

        # Request and process scoot data for all hour
        for h_time in rrule.rrule(
            rrule.HOURLY,
            dtstart=start_hour,
            until=self.end_datetime - timedelta(hours=1),
        ):
            self.process_hour(h_time)

        # Summarise updates
        self.logger.info(
            "Committed %s records to table %s in %s",
            green(n_records_inserted),
            green(ScootReading.__tablename__),
            green(duration(start_update, time.time())),
        )
