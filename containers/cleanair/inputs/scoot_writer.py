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
from ..timestamps import unix_from_str, utcstr_from_unix


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
        self.csv_columns = ["TimestampMin", "DetectorID", "DetectorFault", "NVehiclesInInterval",
                            "OccupancyPercentage", "CongestionPercentage", "SaturationPercentage", "FlowRawCount",
                            "OccupancyRawCount", "CongestionRawCount", "SaturationRawCount", "Region"]

        # How many minutes to combine into a single reading (to reduce how much is written to the database)
        self.aggregation_size = 60

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

    def get_batched_remote_files(self):
        """Get batched list of remote files grouped by aggregation"""
        file_list = []
        for date in rrule.rrule(rrule.DAILY, dtstart=self.start_date, until=self.end_date):
            year, month, day = date.strftime(r"%Y-%m-%d").split("-")
            for timestring in [str(h).zfill(2) + str(m).zfill(2) for h in range(24) for m in range(60)]:
                csv_name = "{y}{m}{d}-{timestring}.csv".format(y=year, m=month, d=day, timestring=timestring)
                file_list.append(("Control/TIMSScoot/{y}/{m}/{d}".format(y=year, m=month, d=day), csv_name))
                if len(file_list) == self.aggregation_size:
                    yield file_list
                    file_list = []
        if file_list:
            yield file_list

    def aggregate_detector_readings(self, filebatch):
        """Request all readings between {start_date} and {end_date}, removing duplicates."""
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
                                               "TimestampMin": lambda x: unix_from_str(x, timezone="Europe/London"),
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
                self.logger.info("Loaded readings from %s", green(filename))

        # Aggregate a batch of dataframes from a single time period
        self.logger.info("Aggregating readings from %s CSV files into a single reading per site",
                         green(len(processed_readings)))
        df_comb = self.combine_by_detector_id(processed_readings)

        # Construct the measurement dates - ensure that all readings in this set use the same start and end times
        self.logger.debug("Converting date format to UTC and rounding to the closest hour")
        df_comb["MeasurementStartUTC"] = df_comb["TimestampMin"].apply(lambda x: utcstr_from_unix(x, rounded=True))
        df_comb["MeasurementEndUTC"] = df_comb["TimestampMax"].apply(lambda x: utcstr_from_unix(x, rounded=True))
        df_comb["MeasurementStartUTC"].values[:] = df_comb.mode()["MeasurementStartUTC"][0]  # use modal value
        df_comb["MeasurementEndUTC"].values[:] = df_comb.mode()["MeasurementEndUTC"][0]  # use modal value

        # Drop temporary columns
        df_comb.drop(["DetectorFault", "TimestampMin", "TimestampMax"], axis=1, inplace=True)

        # Return the dataframe as a list of dictionaries
        return list(df_comb.T.to_dict().values())

    def combine_by_detector_id(self, input_dfs):
        """Aggregate measurements by detector ID across several readings"""
        # Combine batch into one dataframe then
        df_comb = pandas.concat(input_dfs, ignore_index=True)
        df_comb["TimestampMax"] = df_comb["TimestampMin"]
        # Group by DetectorID: each column has its own combination rule
        try:
            # Scale all summed variables to correct for possible missing values from detector faults
            # combined_df = df_comb.groupby(["DetectorID"]).agg(
            return df_comb.groupby(["DetectorID"]).agg(
                {
                    "TimestampMin": "min",
                    "TimestampMax": "max",
                    "DetectorID": "first",
                    "DetectorFault": any,
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
            return pandas.DataFrame(columns=df_comb.columns)

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

                # Add readings to the database session
                # The following database operations can be slow. However, with the switch to hourly data they are not
                # problematic. In contrast to the claims at https://docs.sqlalchemy.org/en/13/faq/performance.html,
                # using bulk insertions does not provide a speed-up but does increase the risk of dataloss. We are
                # therefore sticking to the higher-level functions here. Use of flush() provides the check-point
                # behaviour that we were previously looking for.
                self.logger.info("Inserting %s records to database session", green(len(site_readings)))
                start_insert = time.time()
                try:
                    session.add_all([scoot_tables.ScootReading(**site_reading) for site_reading in site_readings])
                    session.flush()
                    n_records += len(site_readings)
                except IntegrityError as err:
                    self.logger.error("Ignoring attempt to insert duplicate records!")
                    self.logger.error(str(err))
                    session.rollback()
                self.logger.info("Insertion took %s seconds", green("{:.2f}".format(time.time() - start_insert)))

            # Commit changes
            self.logger.info("Committing %s records to database table %s",
                             green(n_records), green(scoot_tables.ScootReading.__tablename__))
            session.commit()
        self.logger.info("Finished %s readings update", green("Scoot"))
        self.logger.info("Full database interaction took %s minutes",
                         green("{:.2f}".format((time.time() - start_session) / 60.)))
