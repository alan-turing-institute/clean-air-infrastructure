"""
Get data from the LAQN network via the API maintained by Kings College London:
  (https://www.londonair.org.uk/Londonair/API/)
"""
import requests
from .databases import Updater, scoot_tables
from .loggers import green
import boto3
import botocore
import datetime
# from dateutil.rrule import rrule, DAILY
from dateutil import rrule
import os
import csv
import pytz
import pandas as pd

# import botocore

class ScootDatabase(Updater):
    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Set up AWS access keys
        self.key_id = "********"
        self.secure_key = "********"

        # Set up the known column names
        self.csv_columns = ["MeasurementDateUTC", "DetectorID", "DetectorFault", "FlowThisMinute",
                            "OccupancyPercentage", "CongestionPercentage", "SaturationPercentage", "FlowRawCount",
                            "OccupancyRawCount", "CongestionRawCount", "SaturationRawCount", "Region"]

        # How many CSV files to combine into a single batch commit (15768 entries per CSV file)
        self.commit_batch_size = 10


        # Ensure that tables exist
        scoot_tables.initialise(self.dbcnxn.engine)

    def request_site_entries(self):
        """SCOOT sites are available as static data and cannot be dynamically loaded"""
        self.logger.error("ScootDatabase.request_site_entries should never be called!")

    def get_remote_file_list(self):
        """Get full list of remote files"""
        file_list = []
        for date in rrule.rrule(rrule.DAILY, dtstart=self.api.start_date, until=self.api.end_date):
            year, month, day = date.strftime(r"%Y-%m-%d").split("-")
            for minute in [str(h).zfill(2)+str(m).zfill(2) for h in range(24) for m in range(60)]:
                csv_name = "{y}{m}{d}-{id}.csv".format(y=year, m=month, d=day, id=minute)
                file_list.append(["Control/TIMSScoot/{y}/{m}/{d}".format(y=year, m=month, d=day), csv_name])
        return file_list



    # def request_site_readings(self, start_date, end_date):
    #     """Request all readings between {start_date} and {end_date}, removing duplicates."""
    #     def convert_tz(timestamp):
    #         # Convert timestamp to UTC
    #         london_tz = pytz.timezone("Europe/London")
    #         timestamp_raw = datetime.datetime.strptime(timestamp.strip(), r"%Y-%m-%d %H:%M:%S")
    #         timestamp_tz = london_tz.localize(timestamp_raw)
    #         return timestamp_tz.astimezone(pytz.utc).strftime(r"%Y-%m-%d %H:%M:%S")

    #     # Set up the known column names
    #     column_names = ["MeasurementDateUTC", "DetectorID", "DetectorFault", "FlowThisMinute", "OccupancyPercentage",
    #                     "CongestionPercentage", "SaturationPercentage", "FlowRawCount", "OccupancyRawCount",
    #                     "CongestionRawCount", "SaturationRawCount", "Region"]

    #     # Get an AWS client
    #     client = boto3.client("s3", aws_access_key_id=self.key_id, aws_secret_access_key=self.secure_key)


    #     # Parse all of the CSV files into dataframes and return these as a list
    #     processed_readings = []
    #     for date in rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date):
    #         year, month, day = date.strftime(r"%Y-%m-%d").split("-")
    #         for minute in [str(h).zfill(2)+str(m).zfill(2) for h in range(24) for m in range(60)]:
    #             csv_name = "{y}{m}{d}-{id}.csv".format(y=year, m=month, d=day, id=minute)
    #             try:
    #                 client.download_file("surface.data.tfl.gov.uk",
    #                                      "Control/TIMSScoot/{y}/{m}/{d}/{f}".format(y=year, m=month, d=day, f=csv_name),
    #                                      csv_name)
    #                 # Read the CSV files into a dataframe
    #                 scoot_df = pd.read_csv(csv_name, names=column_names, skipinitialspace=True,
    #                                     converters={
    #                                         "MeasurementDateUTC": convert_tz,
    #                                         "FlowThisMinute": lambda x: float(x) / 60,
    #                                         "DetectorFault": lambda x: x.strip() == "Y",
    #                                         "Region": lambda x: x.strip()
    #                                         })
    #                 processed_readings.append(scoot_df)
    #             except botocore.exceptions.ClientError:
    #                 self.logger.error("Failed to retrieve %s. Possibly this file does not exist yet", csv_name)
    #                 continue
    #             finally:
    #                 if os.path.isfile(csv_name):
    #                     os.remove(csv_name)
    #                 self.logger.info("Finished processing %s", csv_name)
    #     self.logger.info("Retrieved %i time-sliced CSV files", len(processed_readings))
    #     return processed_readings

    def retrieve_site_readings(self, client, filepath, filename):
        """Retrieve site readings as a list of dictionaries"""
        def convert_tz(timestamp):
            """Convert timestamp to UTC"""
            london_tz = pytz.timezone("Europe/London")
            timestamp_raw = datetime.datetime.strptime(timestamp.strip(), r"%Y-%m-%d %H:%M:%S")
            timestamp_tz = london_tz.localize(timestamp_raw)
            return timestamp_tz.astimezone(pytz.utc).strftime(r"%Y-%m-%d %H:%M:%S")
        # Process site readings from AWS storage
        processed_readings = []
        try:
            client.download_file("surface.data.tfl.gov.uk",
                                 "{path}/{file}".format(path=filepath, file=filename),
                                 filename)
            # Read the CSV file into a dataframe
            scoot_df = pd.read_csv(filename, names=self.csv_columns, skipinitialspace=True,
                                   converters={
                                       "MeasurementDateUTC": convert_tz,
                                       "FlowThisMinute": lambda x: float(x) / 60,
                                       "DetectorFault": lambda x: x.strip() == "Y",
                                       "Region": lambda x: x.strip()
                                   })
            processed_readings = list(scoot_df.T.to_dict().values())
        except botocore.exceptions.ClientError:
            self.logger.error("Failed to retrieve %s. Possibly this file does not exist yet", filename)
        finally:
            if os.path.isfile(filename):
                os.remove(filename)
            self.logger.info("Extracted %i records from %s", len(processed_readings), filename)
        return processed_readings


    def update_site_list_table(self):
        """"SCOOT sites are available as static data and cannot be dynamically loaded"""
        self.logger.error("ScootDatabase.update_site_list_table should never be called!")

    def update_reading_table(self):
        """Update the database with new traffic data."""
        self.logger.info("Starting Scoot data update...")

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


        # Open a DB session and commit these changes
        with self.dbcnxn.open_session() as session:

            # Since the individual CSV files contain a lot of data, we cannot keep everything in memory so we split
            # the transaction into several stages
            self.logger.info("Requesting readings from %s for all sites", green("TfL AWS storage"))

            # Get an AWS client
            client = boto3.client("s3", aws_access_key_id=self.key_id, aws_secret_access_key=self.secure_key)

            # For each identified file, retrieve the readings and add them to the database session
            n_records, n_files = 0, 0
            for filepath, filename in self.get_remote_file_list():
                site_readings = self.retrieve_site_readings(client, filepath, filename)
                session.add_all([scoot_tables.build_reading_entry(site_reading) for site_reading in site_readings])
                n_records += len(site_readings)
                n_files += 1

            # Commit changes
            self.logger.info("Committing %i records from %i files to database table %s",
                            green(n_records), green(n_files),
                            green(scoot_tables.ScootReading.__tablename__))
            session.commit()