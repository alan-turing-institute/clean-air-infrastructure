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
from ..databases import Updater, scoot_tables
from ..loggers import green
from ..timestamps import datetime_from_unix, unix_from_str, utcstr_from_datetime


class ScootWriter(Updater):
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
        self.csv_columns = ["Timestamp", "DetectorID", "DetectorFault", "NVehiclesInInterval",
                            "OccupancyPercentage", "CongestionPercentage", "SaturationPercentage", "FlowRawCount",
                            "OccupancyRawCount", "CongestionRawCount", "SaturationRawCount", "Region"]

        # Start with an empty list of detector IDs
        self.detector_ids = []

        # Ensure that tables exist
        scoot_tables.initialise(self.dbcnxn.engine)

        # Ensure that postgis has been enabled
        self.dbcnxn.ensure_postgis()

    def request_site_entries(self):
        """Get list of known detectors"""
        with self.dbcnxn.open_session() as session:
            scootdetectors = Table("scootdetectors", scoot_tables.ScootReading.metadata, schema="datasources",
                                   autoload=True, autoload_with=self.dbcnxn.engine)
            detectors = sorted([s[0] for s in session.query(scootdetectors.c.detector_n).distinct()])
        return detectors

    def get_remote_filenames(self):
        """Get all possible remote file details for the period in question"""
        file_list = []
        for date in rrule.rrule(rrule.DAILY, dtstart=self.start_datetime, until=self.end_datetime):
            year, month, day = date.strftime(r"%Y-%m-%d").split("-")
            for timestring in [str(h).zfill(2) + str(m).zfill(2) for h in range(24) for m in range(60)]:
                csv_name = "{y}{m}{d}-{timestring}.csv".format(y=year, m=month, d=day, timestring=timestring)
                file_list.append(("Control/TIMSScoot/{y}/{m}/{d}".format(y=year, m=month, d=day), csv_name))
        return file_list

    def validate_remote_data(self):
        """
        Request all readings between {start_date} and {end_date}.
        Remove readings with unknown detector ID or detector faults.
        """
        start_aws = time.time()
        self.logger.info("This will take approximately 20 minutes...")

        # Get an AWS client
        client = boto3.client("s3", aws_access_key_id=self.access_key_id, aws_secret_access_key=self.access_key)

        # Parse each CSV file into a dataframe and add these to a list
        processed_readings = []
        for filepath, filename in self.get_remote_filenames():
            try:
                client.download_file("surface.data.tfl.gov.uk",
                                     "{path}/{file}".format(path=filepath, file=filename),
                                     filename)
                # Read the CSV files into a dataframe
                scoot_df = pandas.read_csv(filename, names=self.csv_columns, skipinitialspace=True,
                                           converters={
                                               "Timestamp": lambda x: unix_from_str(x, timezone="Europe/London"),
                                               "NVehiclesInInterval": lambda x: float(x) / 60,
                                               "DetectorFault": lambda x: x.strip() == "Y",
                                               "Region": lambda x: x.strip(),
                                           })
                # Remove any sites that are not in our site database
                scoot_df = scoot_df[scoot_df["DetectorID"].isin(self.detector_ids)]
                # Remove any readings with detector faults
                scoot_df = scoot_df[~scoot_df["DetectorFault"]]
                # Append to list of readings
                processed_readings.append(scoot_df)
            except botocore.exceptions.ClientError:
                self.logger.error("Failed to retrieve %s. Possibly this file does not exist yet", filename)
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
        # Group by DetectorID: each column has its own combination rule
        try:
            # Scale all summed variables to correct for possible missing values from detector faults
            return input_df.groupby(["DetectorID"]).agg(
                {
                    "DetectorID": "first",
                    "NVehiclesInInterval": lambda x: sum(x) * (60. / len(x)),
                    "OccupancyPercentage": "mean",
                    "CongestionPercentage": "mean",
                    "SaturationPercentage": "mean",
                    "FlowRawCount": lambda x: sum(x) * (60. / len(x)),
                    "OccupancyRawCount": lambda x: sum(x) * (60. / len(x)),
                    "CongestionRawCount": lambda x: sum(x) * (60. / len(x)),
                    "SaturationRawCount": lambda x: sum(x) * (60. / len(x)),
                    "Region": "first",
                })
        except pandas.core.base.DataError:
            self.logger.warning("Data aggregation failed - returning an empty dataframe")
            return pandas.DataFrame(columns=input_df.columns)

    def update_remote_tables(self):
        """Update the database with new Scoot traffic data."""
        self.logger.info("Starting %s readings update...", green("Scoot"))
        start_update = time.time()

        # Get the list of known detectors
        self.detector_ids = self.request_site_entries()

        # Load readings from AWS
        self.logger.info("Requesting readings from %s for %s sites",
                         green("TfL AWS storage"), green(len(self.detector_ids)))

        # Load all valid remote data into a single dataframe
        df_processed = self.validate_remote_data()

        # Get the minimum and maximum time in the dataset
        time_min = datetime_from_unix(df_processed["Timestamp"].min())
        time_max = datetime_from_unix(df_processed["Timestamp"].max())

        n_records = 0
        # Slice processed data into hourly chunks and aggregate these by detector ID
        for start_time in rrule.rrule(rrule.HOURLY,
                                      dtstart=time_min.replace(minute=0, second=0, microsecond=0),
                                      until=time_max):
            end_time = start_time + datetime.timedelta(hours=1)

            # Construct hourly data
            self.logger.info("Processing data between %s and %s", green(start_time), green(end_time))
            df_hourly = df_processed.loc[(df_processed["Timestamp"] > start_time.timestamp()) &
                                         (df_processed["Timestamp"] <= end_time.timestamp())].copy()

            # Drop unused columns and aggregate
            self.logger.info("Aggregating %s readings by site", green(df_hourly.shape[0]))
            df_hourly.drop(["DetectorFault", "Timestamp"], axis=1, inplace=True)
            df_aggregated = self.combine_by_detector_id(df_hourly)

            # Add timestamps
            df_aggregated["MeasurementStartUTC"] = utcstr_from_datetime(start_time)
            df_aggregated["MeasurementEndUTC"] = utcstr_from_datetime(end_time)

            # Add readings to database
            start_session = time.time()
            site_readings = list(df_aggregated.T.to_dict().values())
            self.logger.info("Inserting %s per-site records into database", green(len(site_readings)))

            # The following database operations can be slow. However, with the switch to hourly data they are not
            # problematic. In contrast to the claims at https://docs.sqlalchemy.org/en/13/faq/performance.html,
            # using bulk insertions does not provide a speed-up but does increase the risk of data loss. We are
            # therefore sticking to the higher-level functions here.
            with self.dbcnxn.open_session() as session:
                try:
                    session.add_all([scoot_tables.ScootReading(**site_reading) for site_reading in site_readings])
                    session.commit()
                    n_records += len(site_readings)
                except IntegrityError as err:
                    self.logger.error("Ignoring attempt to insert duplicate records!")
                    self.logger.error(str(err))
                    session.rollback()
            self.logger.info("Insertion took %s seconds", green("{:.2f}".format(time.time() - start_session)))

        # Summarise updates
        self.logger.info("Committed %s records to table %s in %s minutes",
                         green(n_records),
                         green(scoot_tables.ScootReading.__tablename__),
                         green("{:.2f}".format((time.time() - start_update) / 60.)))
