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
import pytz
from ..databases import Updater, scoot_tables
from ..loggers import green


class ScootDatabase(Updater):
    """
    Class to get data from the Scoot traffic detector network via the S3 bucket maintained by TfL:
    (https://s3.console.aws.amazon.com/s3/buckets/surface.data.tfl.gov.uk)
    """
    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Set up AWS access keys
        try:
            self.access_key_id = kwargs["aws_key_id"]
            self.access_key = kwargs["aws_key"]
        except KeyError:
            raise IOError("No AWS connection details were provided!")

        # Set up the known column names
        self.csv_columns = ["Timestamp", "DetectorID", "DetectorFault", "FlowThisInterval",
                            "OccupancyPercentage", "CongestionPercentage", "SaturationPercentage", "FlowRawCount",
                            "OccupancyRawCount", "CongestionRawCount", "SaturationRawCount", "Region"]

        # How many minutes to combine into a single reading (to reduce how much is written to the database)
        self.aggregation_size = 5

        # How many aggregated readings to batch into a single database transaction
        self.transaction_batch_size = 12

        # Start with an empty list of detector IDs
        self.detector_ids = []

        # Ensure that tables exist
        scoot_tables.initialise(self.dbcnxn.engine)

    def request_site_entries(self):
        """Get list of known detectors"""
        with self.dbcnxn.open_session() as session:
            scootdetectors = Table("scootdetectors", scoot_tables.ScootReading.metadata,
                                   autoload=True, autoload_with=self.dbcnxn.engine)
            detectors = sorted([s[0] for s in session.query(scootdetectors.c.detector_n).distinct()])
        return detectors

    def get_batched_remote_files(self):
        """Get batched list of remote files grouped by aggregation"""
        file_list = []
        for date in rrule.rrule(rrule.DAILY, dtstart=self.start_date, until=self.end_date):
            year, month, day = date.strftime(r"%Y-%m-%d").split("-")
            for minute in [str(h).zfill(2) + str(m).zfill(2) for h in range(24) for m in range(60)]:
                csv_name = "{y}{m}{d}-{id}.csv".format(y=year, m=month, d=day, id=minute)
                file_list.append(("Control/TIMSScoot/{y}/{m}/{d}".format(y=year, m=month, d=day), csv_name))
                if len(file_list) == self.aggregation_size:
                    yield file_list
                    file_list = []
        if file_list:
            yield file_list

    def aggregate(self, input_dfs):
        """Aggregate measurements across several minutes"""
        # Combine batch into one dataframe then
        df_combined = pandas.concat(input_dfs, ignore_index=True)
        # Group by DetectorID: each column has its own combination rule
        try:
            return df_combined.groupby(["DetectorID"]).agg(
                {
                    "Timestamp": lambda x: int(sum(x) / len(x)),
                    "DetectorID": "first",
                    "DetectorFault": any,
                    "FlowThisInterval": "sum",
                    "IntervalMinutes": "sum",
                    "OccupancyPercentage": "mean",
                    "CongestionPercentage": "mean",
                    "SaturationPercentage": "mean",
                    "FlowRawCount": "sum",
                    "OccupancyRawCount": "sum",
                    "CongestionRawCount": "sum",
                    "SaturationRawCount": "count",
                    "Region": "first",
                })
        except pandas.core.base.DataError:
            self.logger.warning("Data aggregation failed - returning an empty dataframe")
            return pandas.DataFrame(columns=df_combined.columns)

    def aggregate_detector_readings(self, filebatch):
        """Request all readings between {start_date} and {end_date}, removing duplicates."""
        def to_unix(naive_string):
            # Convert naive string to unix timestamp
            london_tz = pytz.timezone("Europe/London")
            timestamp_naive = datetime.datetime.strptime(naive_string.strip(), r"%Y-%m-%d %H:%M:%S")
            timestamp_aware = london_tz.localize(timestamp_naive)
            return timestamp_aware.timestamp()

        def to_utc_string(timestamp):
            # Convert unix timestamp to UTC string
            return datetime.datetime.fromtimestamp(timestamp, pytz.utc).strftime(r"%Y-%m-%d %H:%M:%S")

        # Get an AWS client
        client = boto3.client("s3", aws_access_key_id=self.access_key_id, aws_secret_access_key=self.access_key)

        # Parse each CSV file into a dataframe and add these to a list
        processed_readings = []
        for filepath, filename in filebatch:
            try:
                client.download_file("surface.data.tfl.gov.uk",
                                     "{path}/{file}".format(path=filepath, file=filename),
                                     filename)
                # Read the CSV files into a dataframe
                scoot_df = pandas.read_csv(filename, names=self.csv_columns, skipinitialspace=True,
                                           converters={
                                               "Timestamp": to_unix,
                                               "FlowThisInterval": lambda x: float(x) / 60,
                                               "DetectorFault": lambda x: x.strip() == "Y",
                                               "Region": lambda x: x.strip(),
                                           })
                # Remove any sites that are not in our site database
                scoot_df = scoot_df[scoot_df["DetectorID"].isin(self.detector_ids)]
                # Set the interval to one minute and append to list of readings
                scoot_df["IntervalMinutes"] = 1
                processed_readings.append(scoot_df)
            except botocore.exceptions.ClientError:
                self.logger.error("Failed to retrieve %s. Possibly this file does not exist yet", filename)
                continue
            finally:
                if os.path.isfile(filename):
                    os.remove(filename)
                self.logger.info("Loaded readings from %s", green(filename))

        # Aggregate a batch of consecutive dataframes
        self.logger.info("Aggregating %s CSV files into one measurement", green(len(processed_readings)))
        df_combined = self.aggregate(processed_readings)

        # Construct the measurement date and drop the timestamp
        self.logger.debug("Converting date format to UTC")
        df_combined["MeasurementDateUTC"] = df_combined["Timestamp"].apply(to_utc_string)
        df_combined.drop(["Timestamp"], axis=1, inplace=True)

        # Drop the timestamp and return the dataframe as a list of dictionaries
        return list(df_combined.T.to_dict().values())

    def update_site_list_table(self):
        """"SCOOT sites are available as static data and cannot be dynamically loaded"""
        self.logger.error("ScootDatabase.update_site_list_table should never be called!")

    def update_remote_tables(self):
        """Update the database with new Scoot traffic data."""
        self.logger.info("Starting %s readings update...", green("Scoot"))

        # Get the list of known detectors
        self.detector_ids = self.request_site_entries()

        # Load readings from AWS
        self.logger.info("Requesting readings from %s for %s sites",
                         green("TfL AWS storage"), green(len(self.detector_ids)))

        # Open a DB session
        start_session = time.time()
        with self.dbcnxn.open_session() as session:
            n_records = 0

            # Retrieve files from AWS. Since these CSV files contain very granular data (once per minute) we aggregate
            # into five-minute chunks (controlled by self.aggregation_size)
            for filebatch in self.get_batched_remote_files():
                # Retrieve aggregated detector readings for this batch of files
                site_readings = self.aggregate_detector_readings(filebatch)

                # Add readings to the database session - use bulk_insert_mappings to reduce the ORM overhead
                # In contrast to the claims at https://docs.sqlalchemy.org/en/13/faq/performance.html this does not seem
                # to result in a speed-up, but it does provide regular check-points meaning that the final commit
                # operation takes minutes rather than hours.
                self.logger.info("Adding %i record inserts to database session", len(site_readings))
                start_insert = time.time()
                try:
                    session.bulk_insert_mappings(scoot_tables.ScootReading, site_readings)
                    n_records += len(site_readings)
                except IntegrityError:
                    self.logger.error("Ignoring attempt to insert duplicate records!")
                    session.rollback()
                self.logger.info("Insertion took %.2f seconds", time.time() - start_insert)

            # Commit changes
            self.logger.info("Committing %s records to database table %s",
                             green(n_records),
                             green(scoot_tables.ScootReading.__tablename__))
            session.commit()
        self.logger.info("Finished %s readings update", green("Scoot"))
        self.logger.info("Full database interaction took %.2f minutes", (time.time() - start_session) / 60.)
