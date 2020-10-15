"""
Retrieve and process data from the SCOOT traffic detector network
"""

from typing import List, Tuple, Any
import datetime
from datetime import timedelta
import os
import time
from dateutil import rrule
import boto3
import botocore
import pandas as pd
import pytz
from sqlalchemy import func, Table
from ..databases import DBWriter
from ..databases.tables import ScootReading
from ..decorators import db_query
from ..loggers import get_logger, green, duration, duration_from_seconds
from ..mixins import DateRangeMixin, DBQueryMixin
from ..timestamps import datetime_from_unix, unix_from_str, utcstr_from_datetime


class ScootWriter(DateRangeMixin, DBWriter, DBQueryMixin):
    """
    Class to get data from the SCOOT traffic detector network via the S3 bucket maintained by TfL:
    (https://s3.console.aws.amazon.com/s3/buckets/surface.data.tfl.gov.uk)
    """

    def __init__(
        self, aws_key_id: str, aws_key: str, detector_ids: List[str] = None, **kwargs
    ) -> None:
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
    def get_existing_scoot_data(self) -> Any:
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
    def get_remote_filenames(
        start_datetime_utc: datetime.datetime, end_datetime_utc: datetime.datetime
    ) -> List[Tuple[str, str]]:
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
            rrule.HOURLY,
            dtstart=start_datetime,
            until=end_datetime - datetime.timedelta(hours=1),
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

    def request_remote_data(
        self,
        start_datetime_utc: datetime.datetime,
        end_datetime_utc: datetime.datetime,
        detector_ids: List[str],
    ) -> List[pd.DataFrame]:
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

    def aggregate_scoot_data(self, df_readings: pd.DataFrame) -> pd.DataFrame:
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
            rrule.HOURLY,
            dtstart=start_hour,
            until=self.end_datetime - timedelta(hours=1),
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

                expected_readings = pd.DataFrame(
                    [
                        {
                            "detector_id": i,
                            "measurement_start_utc": utcstr_from_datetime(
                                start_datetime_utc.replace(tzinfo=datetime.timezone.utc)
                            ),
                            "measurement_end_utc": utcstr_from_datetime(
                                end_datetime_utc.replace(tzinfo=datetime.timezone.utc)
                            ),
                        }
                        for i in unprocessed_detectors
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
                    len(unprocessed_detectors),
                    n_readings - n_null,
                    n_readings,
                    n_null,
                )

                site_records = expected_merged.to_dict("records")

                # Drop NAN values from dictionary. They will insert to DB as Null
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

                start_session = time.time()

                # Commit the records to the database
                self.commit_records(
                    site_record_drop_null, on_conflict="overwrite", table=ScootReading,
                )
                n_records_inserted += len(site_record_drop_null)

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
