"""
Get data from the LAQN network via the API maintained by Kings College London:
  (https://www.londonair.org.uk/Londonair/API/)
"""
from sqlalchemy import Table
import requests
from .databases import Updater, scoot_tables
from .loggers import green
import boto3
import botocore
import datetime
from dateutil import rrule
import os
import csv
import pytz
import pandas as pd
from itertools import zip_longest

# import botocore

class ScootDatabase(Updater):
    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Set up AWS access keys
        self.key_id = "********"
        self.secure_key = "********"

        # Set up the known column names
        self.csv_columns = ["Timestamp", "DetectorID", "DetectorFault", "FlowThisInterval",
                            "OccupancyPercentage", "CongestionPercentage", "SaturationPercentage", "FlowRawCount",
                            "OccupancyRawCount", "CongestionRawCount", "SaturationRawCount", "Region"]

        # How many minutes to combine into a single reading (to reduce how much is written to the database)
        self.aggregation_size = 5

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

    @staticmethod
    def get_remote_file_list(start_date, end_date):
        """Get full list of remote files"""
        file_list = []
        for date in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date):
            year, month, day = date.strftime(r"%Y-%m-%d").split("-")
            # for minute in [str(h).zfill(2)+str(m).zfill(2) for h in range(24) for m in range(60)]:
            for minute in [str(h).zfill(2)+str(m).zfill(2) for h in range(1) for m in range(60)]:
                csv_name = "{y}{m}{d}-{id}.csv".format(y=year, m=month, d=day, id=minute)
                file_list.append(["Control/TIMSScoot/{y}/{m}/{d}".format(y=year, m=month, d=day), csv_name])
        return file_list

    def aggregate(self, input_dfs, batch_size):
        """Combine dataframes into a batch"""
        output_dfs = []
        for df_batch in zip_longest(*[iter(input_dfs)] * batch_size):
            df_batch = [df for df in df_batch if df is not None]
            if len(df_batch) != batch_size:
                self.logger.warning("Combining last {} readings into one batch".format(len(df_batch)))
            # Combine batch into one dataframe then group by DetectorID
            # Each column has its own combination rule
            print("before", len(input_dfs))
            df_combined = pd.concat(df_batch, ignore_index=True)
            output_dfs.append(df_combined.groupby(["DetectorID"]).agg(
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
                }
            ))
            del df_batch
            print("after", len(input_dfs))
        return output_dfs

    def request_site_readings(self, start_date, end_date, batch_size=None):
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
        client = boto3.client("s3", aws_access_key_id=self.key_id, aws_secret_access_key=self.secure_key)

        # Parse each CSV file into a dataframe and add these to a list
        processed_readings = []
        for filepath, filename in self.get_remote_file_list(start_date, end_date):
            try:
                client.download_file("surface.data.tfl.gov.uk",
                                     "{path}/{file}".format(path=filepath, file=filename),
                                     filename)
                # Read the CSV files into a dataframe
                scoot_df = pd.read_csv(filename, names=self.csv_columns, skipinitialspace=True,
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
                self.logger.info("Finished processing %s", filename)
        self.logger.info("Retrieved %i time-sliced CSV files", len(processed_readings))

        # Aggregate consecutive dataframes if requested
        if batch_size:
            self.logger.info("Combining CSV files into batches of %i", batch_size)
            processed_readings = self.aggregate(processed_readings, batch_size)

        # Combine the readings and construct the measurement date
        df_combined = pd.concat(processed_readings, ignore_index=True)
        df_combined["MeasurementDateUTC"] = df_combined["Timestamp"].apply(to_utc_string)

        # Drop the timestamp and return the dataframe as a list of dictionaries
        df_combined.drop(["Timestamp"], axis=1, inplace=True)
        return list(df_combined.T.to_dict().values())


    # def retrieve_site_readings(self, client, filepath, filename):
    #     """Retrieve site readings as a list of dictionaries"""
    #     def convert_tz(timestamp):
    #         """Convert timestamp to UTC"""
    #         london_tz = pytz.timezone("Europe/London")
    #         timestamp_raw = datetime.datetime.strptime(timestamp.strip(), r"%Y-%m-%d %H:%M:%S")
    #         timestamp_tz = london_tz.localize(timestamp_raw)
    #         return timestamp_tz.astimezone(pytz.utc).strftime(r"%Y-%m-%d %H:%M:%S")
    #     # Process site readings from AWS storage
    #     processed_readings = []
    #     try:
    #         client.download_file("surface.data.tfl.gov.uk",
    #                              "{path}/{file}".format(path=filepath, file=filename),
    #                              filename)
    #         # Read the CSV file into a dataframe
    #         scoot_df = pd.read_csv(filename, names=self.csv_columns, skipinitialspace=True,
    #                                converters={
    #                                    "MeasurementDateUTC": convert_tz,
    #                                    "FlowThisInterval": lambda x: float(x) / 60,
    #                                    "DetectorFault": lambda x: x.strip() == "Y",
    #                                    "Region": lambda x: x.strip()
    #                                })
    #         processed_readings = list(scoot_df.T.to_dict().values())
    #     except botocore.exceptions.ClientError:
    #         self.logger.error("Failed to retrieve %s. Possibly this file does not exist yet", filename)
    #     finally:
    #         if os.path.isfile(filename):
    #             os.remove(filename)
    #         self.logger.info("Extracted %i records from %s", len(processed_readings), filename)
    #     return processed_readings


    def update_site_list_table(self):
        """"SCOOT sites are available as static data and cannot be dynamically loaded"""
        self.logger.error("ScootDatabase.update_site_list_table should never be called!")

    def update_reading_table(self):
        """Update the database with new traffic data."""
        self.logger.info("Starting %s readings update...", green("Scoot"))

        # # Since the individual CSV files contain a lot of data, we cannot keep everything in memory so we split
        # # the transaction into several stages
        # self.logger.info("Requesting readings from %s for all sites", green("TfL AWS storage"))

        # # Get an AWS client
        # client = boto3.client("s3", aws_access_key_id=self.key_id, aws_secret_access_key=self.secure_key)

        # # For each identified file, retrieve the readings and add them to the database session
        # n_records, n_files = 0, 0
        # current_batch,
        # for filepath, filename in self.get_remote_file_list():
        #     site_readings = self.retrieve_site_readings(client, filepath, filename)

        #     # Open a DB session and commit these changes
        #     with self.dbcnxn.open_session() as session:
        #         session.add_all([scoot_tables.build_reading_entry(site_reading) for site_reading in site_readings])
        #         session.commit()
        #         n_records += len(site_readings)
        #         n_files += 1

        # # Finalise
        # self.logger.info("Committed %i records from %i files to database table %s",
        #                  green(n_records), green(n_files),
        #                  green(scoot_tables.ScootReading.__tablename__))


        # # Open a DB session and commit these changes
        # with self.dbcnxn.open_session() as session:

        #     # Since the individual CSV files contain a lot of data, we cannot keep everything in memory so we split
        #     # the transaction into several stages
        #     self.logger.info("Requesting readings from %s for all sites", green("TfL AWS storage"))

        #     # Get an AWS client
        #     client = boto3.client("s3", aws_access_key_id=self.key_id, aws_secret_access_key=self.secure_key)

        #     # For each identified file, retrieve the readings and add them to the database session
        #     n_records, n_files = 0, 0
        #     for filepath, filename in self.get_remote_file_list():
        #         site_readings = self.retrieve_site_readings(client, filepath, filename)
        #         session.add_all([scoot_tables.build_reading_entry(site_reading) for site_reading in site_readings])
        #         n_records += len(site_readings)
        #         n_files += 1

        #     # Commit changes
        #     self.logger.info("Committing %i records from %i files to database table %s",
        #                     green(n_records), green(n_files),
        #                     green(scoot_tables.ScootReading.__tablename__))
        #     session.commit()

        # Get the list of known detectors
        self.detector_ids = self.request_site_entries()

        # Open a DB session and commit these changes
        with self.dbcnxn.open_session() as session:
            # Since the individual CSV files contain a lot of data, we cannot keep everything in memory so we split
            # the transaction into several stages
            self.logger.info("Requesting readings from %s for %s sites",
                             green("TfL AWS storage"), green(len(self.detector_ids)))

            # Retrieve detector readings and update the database, batching consecutive readings to reduce data size
            site_readings = self.request_site_readings(self.api.start_date, self.api.end_date,
                                                       batch_size=self.aggregation_size)
            session.add_all([scoot_tables.build_reading_entry(site_reading) for site_reading in site_readings])

            # Commit changes
            self.logger.info("Committing %s records to database table %s",
                            green(len(site_readings)),
                            green(scoot_tables.ScootReading.__tablename__))
            session.commit()
        self.logger.info("Finished %s readings update...", green("Scoot"))
