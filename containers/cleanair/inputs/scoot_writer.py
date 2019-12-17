"""
Scoot
"""
import datetime
import os
import time
from dateutil import rrule
from sqlalchemy import Table
from sqlalchemy.exc import IntegrityError
import boto3
import botocore
import pandas
from ..databases import DBWriter
from ..databases.tables import ScootReading
from ..loggers import get_logger, green
from ..mixins import DateRangeMixin
from ..timestamps import datetime_from_unix, unix_from_str, utcstr_from_datetime


class ScootWriter(DateRangeMixin, DBWriter):
    """
    Class to get data from the Scoot traffic detector network via the S3 bucket maintained by TfL:
    (https://s3.console.aws.amazon.com/s3/buckets/surface.data.tfl.gov.uk)
    """
    def __init__(self, aws_key_id, aws_key, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Set up AWS access keys
        self.access_key_id = aws_key_id
        self.access_key = aws_key

        # Set up the known column names
        self.csv_columns = ["timestamp", "detector_id", "detector_fault", "n_vehicles_in_interval",
                            "occupancy_percentage", "congestion_percentage", "saturation_percentage", "flow_raw_count",
                            "occupancy_raw_count", "congestion_raw_count", "saturation_raw_count", "region"]

        # Start with an empty list of detector IDs
        self.detector_ids = []

    def request_site_entries(self):
        """Get list of known detectors"""
        with self.dbcnxn.open_session() as session:
            scoot_detector = Table("scoot_detector", ScootReading.metadata, schema="interest_points",
                                   autoload=True, autoload_with=self.dbcnxn.engine)
            detectors = sorted([s[0] for s in session.query(scoot_detector.c.detector_n).distinct()])
        return detectors

    def get_remote_filenames(self, start_datetime, end_datetime):
        """Get all possible remote file details for the period in question"""
        file_list = []
        for date in rrule.rrule(rrule.DAILY, dtstart=start_datetime, until=end_datetime):
            year, month, day = date.strftime(r"%Y-%m-%d").split("-")
            for timestring in [str(h).zfill(2) + str(m).zfill(2) for h in range(24) for m in range(60)]:
                csv_name = "{y}{m}{d}-{timestring}.csv".format(y=year, m=month, d=day, timestring=timestring)
                file_list.append(("Control/TIMSScoot/{y}/{m}/{d}".format(y=year, m=month, d=day), csv_name))
        return file_list

    def validate_remote_data(self, start_datetime, end_datetime):
        """
        Request all readings between {start_date} and {end_date}.
        Remove readings with unknown detector ID or detector faults.
        """
        start_aws = time.time()
        self.logger.info("This will take approximately 1 minute for each hour requested...")

        # Get an AWS client
        client = boto3.client("s3", aws_access_key_id=self.access_key_id, aws_secret_access_key=self.access_key)

        # Parse each CSV file into a dataframe and add these to a list
        processed_readings = []
        for filepath, filename in self.get_remote_filenames(start_datetime, end_datetime):
            try:
                self.logger.info("Requesting scoot file %s", filename)
                client.download_file("surface.data.tfl.gov.uk",
                                     "{path}/{file}".format(path=filepath, file=filename),
                                     filename)
                # Read the CSV files into a dataframe
                scoot_df = pandas.read_csv(filename, names=self.csv_columns, skipinitialspace=True,
                                           converters={
                                               "timestamp": lambda x: unix_from_str(x, timezone="Europe/London"),
                                               "n_vehicles_in_interval": lambda x: float(x) / 60,
                                               "detector_fault": lambda x: x.strip() == "Y",
                                               "region": lambda x: x.strip(),
                                           })
                # Remove any sites that are not in our site database
                scoot_df = scoot_df[scoot_df["detector_id"].isin(self.detector_ids)]
                # Remove any readings with detector faults
                scoot_df = scoot_df[~scoot_df["detector_fault"]]
                # Append to list of readings
                processed_readings.append(scoot_df)
            except (botocore.exceptions.ClientError, botocore.exceptions.EndpointConnectionError) as error:
                self.logger.error("Failed to retrieve %s. Error: %s", filename, error)
                continue
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                self.logger.debug("Loaded readings from %s", green(filename))
        # Combine the readings into a single data frame
        df_combined = pandas.concat(processed_readings, ignore_index=True)
        self.logger.info("Loaded %s valid readings in %s minutes",
                         green(df_combined.shape[0]), green("{:.2f}".format((time.time() - start_aws) / 60.)))
        return df_combined

    def combine_by_detector_id(self, input_df):
        """Aggregate measurements by detector ID across several readings"""
        # Group by detector_id: each column has its own combination rule
        try:
            # Scale all summed variables to correct for possible missing values from detector faults
            return input_df.groupby(["detector_id"]).agg(
                {
                    "detector_id": "first",
                    "n_vehicles_in_interval": lambda x: sum(x) * (60. / len(x)),
                    "occupancy_percentage": "mean",
                    "congestion_percentage": "mean",
                    "saturation_percentage": "mean",
                    "flow_raw_count": lambda x: sum(x) * (60. / len(x)),
                    "occupancy_raw_count": lambda x: sum(x) * (60. / len(x)),
                    "congestion_raw_count": lambda x: sum(x) * (60. / len(x)),
                    "saturation_raw_count": lambda x: sum(x) * (60. / len(x)),
                    "region": "first",
                })
        except pandas.core.base.DataError:
            self.logger.warning("Data aggregation failed - returning an empty dataframe")
            return pandas.DataFrame(columns=input_df.columns)

    def aggregate_scoot_data(self, df_processed):

        # Get the minimum and maximum time in the dataset
        time_min = datetime_from_unix(df_processed["timestamp"].min())
        time_max = datetime_from_unix(df_processed["timestamp"].max())

        # Slice processed data into hourly chunks and aggregate these by detector ID
        for start_time in rrule.rrule(rrule.HOURLY,
                                      dtstart=time_min.replace(minute=0, second=0, microsecond=0),
                                      until=time_max):
            end_time = start_time + datetime.timedelta(hours=1)

            # Construct hourly data
            self.logger.info("Processing data between %s and %s", green(start_time), green(end_time))
            df_hourly = df_processed.loc[(df_processed["timestamp"] > start_time.timestamp()) &
                                         (df_processed["timestamp"] <= end_time.timestamp())].copy()

            # Drop unused columns and aggregate
            self.logger.info("Aggregating %s readings by site", green(df_hourly.shape[0]))
            df_hourly.drop(["detector_fault", "timestamp"], axis=1, inplace=True)
            df_aggregated = self.combine_by_detector_id(df_hourly)

            # Add timestamps
            df_aggregated["measurement_start_utc"] = utcstr_from_datetime(start_time)
            df_aggregated["measurement_end_utc"] = utcstr_from_datetime(end_time)

            yield df_aggregated

    def update_remote_tables(self):
        """Update the database with new Scoot traffic data."""
        self.logger.info("Starting %s readings update...", green("Scoot"))
        start_update = time.time()

        # Get the list of known detectors
        self.detector_ids = self.request_site_entries()

        # Load readings from AWS
        self.logger.info("Requesting readings from %s for %s sites",
                         green("TfL AWS storage"), green(len(self.detector_ids)))

        n_records = 0
        # Process a day at a time
        for start_time in rrule.rrule(rrule.DAILY,
                                      dtstart=self.start_datetime,
                                      until=self.end_datetime):
            end_time = start_time + datetime.timedelta(hours=1)

            start_datetime, end_datetime = self.get_datetimes(start_time, end_time)

            # Load all valid remote data into a single dataframe
            df_processed = self.validate_remote_data(start_datetime, end_datetime)

            for df_aggregated in self.aggregate_scoot_data(df_processed):

                # Add readings to database
                start_session = time.time()
                site_records = df_aggregated.to_dict("records")
                self.logger.info("Inserting %s per-site records into database", green(len(site_records)))

                # The following database operations can be slow. However, with the switch to hourly data they are not
                # problematic. In contrast to the claims at https://docs.sqlalchemy.org/en/13/faq/performance.html,
                # using bulk insertions does not provide a speed-up but does increase the risk of data loss. We are
                # therefore sticking to the higher-level functions here.
                with self.dbcnxn.open_session() as session:
                    try:
                        # Commit the records to the database
                        self.add_records(session, site_records, table=ScootReading)
                        session.commit()
                        n_records += len(site_records)
                    except IntegrityError as error:
                        self.logger.error("Failed to add records to the database: %s", type(error))
                        self.logger.error(str(error))
                        session.rollback()
                self.logger.info("Insertion took %s seconds", green("{:.2f}".format(time.time() - start_session)))

        # Summarise updates
        self.logger.info("Committed %s records to table %s in %s minutes",
                         green(n_records),
                         green(ScootReading.__tablename__),
                         green("{:.2f}".format((time.time() - start_update) / 60.)))
