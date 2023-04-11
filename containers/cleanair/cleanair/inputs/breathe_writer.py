
from datetime import datetime, timedelta
import pytz
import io
import requests
import json
from ..mixins.api_request_mixin import APIRequestMixin
from ..mixins.date_range_mixin import DateRangeMixin
from ..mixins.availability_mixins import BreatheAvailabilityMixin
from ..mixins.availability_mixins.breathe_availability import BreatheAvailabilityMixin
from ..databases import DBWriter 
from ..databases.tables.breathe_tables import BreatheSite, BreatheReading
from ..databases.tables import  MetaPoint
from ..loggers import get_logger, green
from ..timestamps import datetime_from_str, utcstr_from_datetime

class BreatheWriter(DateRangeMixin, APIRequestMixin, BreatheAvailabilityMixin, DBWriter):
    """
    Get data from the Breathe London network via the API maintained by Imperial College London:
    (https://www.breathelondon.org/developers)
    """

    def __init__(self,**kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)
        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)
        
    
    def request_site_entries(self):
        """
        Request all Breathe sites
        """

        try:
            endpoint = "https://api.breathelondon.org/api/ListSensors?key=fe47645a-e87a-11eb-9a03-0242ac130003"
            breathe_data = self.get_response(endpoint, timeout=5.0).content
            raw_data = json.loads(io.StringIO(breathe_data).getvalue())[0]
            merged_data = [
                (reading["LatestINO2Value"], reading["LatestIPM25Value"], reading["LatestIPM10Value"])
                for reading in raw_data
                if all(key in reading for key in ["Latitude", "Longitude"])
            ]
            BreatheReading.value = merged_data
            species = [
                [len(reading["LatestINO2Value"]) * "NO2", len(reading["LatestIPM25Value"]) * "PM25", len(reading["LatestIPM10Value"]) * "PM10"]
                for reading in raw_data
                if all(key in reading for key in ["Latitude", "Longitude"])
            ]
            BreatheReading.species_code = species
            return merged_data
        except (json.decoder.JSONDecodeError, requests.exceptions.RequestException, KeyError, TypeError) as e:
            print(f"Error while requesting site entries: {e}")
            return []
    def request_site_readings(self, start_date, end_date, site_code, species, averaging):
        """
        Request all readings for {site_code}, {species} between {start_date} and {end_date} {averaging} eg:hourly
        Remove duplicates and add the site_code
        """
        try:
            # This call retrieves data from Breathe London nodes as a JSON object.
            endpoint = "http://api.breathelondon.org/api/api/getClarityData/{}/{}/{}/{}/{}".format(
                site_code, species, str(start_date), str(end_date), averaging
            )
            sites = self.get_response(endpoint, timeout=120.0).content
            raw_data =sites.decode()
            parsed_data = json.loads(raw_data)
            # Add the site_code
            for reading in parsed_data:
                reading["SiteCode"] = site_code
                species = species
                # Use strptime to convert the string to a datetime object
                start_time = reading["StartDate"]
                date_time_obj = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")
                utc_time = pytz.utc.localize(date_time_obj)
                timestamp_start = utc_time
                timestamp_end = timestamp_start + timedelta(hours=1)
                reading["MeasurementStartUTC"] = timestamp_start.strftime("%Y-%m-%d %H:%M:%S")
                reading["MeasurementEndUTC"] = timestamp_end.strftime("%Y-%m-%d %H:%M:%S")
                breakpoint()
            return parsed_data
        
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed:", endpoint)
            self.logger.warning(error)
            return None
        except (TypeError, KeyError):
            return None

    def update_site_list_table(self):
        """
        Update the breathe_site table
        """
        self.logger.info("Starting Breathe site list update...")

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Reload site information and update the database accordingly
            self.logger.info("Requesting site info from %s", green("API"))

            # Retrieve site entries (discarding any that do not have a known position)
            site_entries = [
                s
                for s in self.request_site_entries()
                if s["Latitude"] and s["Longitude"]
            ]
            for entry in site_entries: 
                entry["geometry"] = MetaPoint.build_ewkt(
                    entry["Latitude"], entry["Longitude"]
                )

            # Only consider unique sites
            unique_sites = {
                s["geometry"]: MetaPoint.build_entry("breathe", geometry=s["geometry"])
                for s in site_entries
            }

            # Update the interest_points table and retrieve point IDs
            point_id = {}
            for geometry, interest_point in unique_sites.items():
                merged_point = session.merge(interest_point)
                session.flush()
                point_id[geometry] = str(merged_point.id)

            # Add point IDs to the site_entries
            for entry in site_entries:
                entry["point_id"] = point_id[entry["geometry"]]

            # Build the site entries and commit
            self.logger.info("Updating site info database records")
            for site in site_entries:
                session.merge(BreatheSite.build_entry(site))
            self.logger.info(
                "Committing changes to database tables %s and %s",
                green(MetaPoint.__tablename__),
                green(BreatheSite.__tablename__),
            )
            session.commit()

    def update_reading_table(self, usecore=True):
        """Update the readings table with new sensor readings."""
        self.logger.info(
            "Starting %s readings update using data from %s to %s...",
            green("Breathe"),
            self.start_datetime,
            self.end_datetime,
        )

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Load readings for all sites and update the database accordingly
            site_info_query = session.query(BreatheSite)
            self.logger.info(
                "Requesting readings from %s for %s sites",
                green("API"),
                green(len(list(site_info_query))),
            )

        # Get all readings for each site between its start and end dates and update the database
        site_readings = self.get_readings_by_site(
            site_info_query, self.start_date, self.end_date
        )
        site_records = [
            BreatheReading.build_entry(site_reading, return_dict=usecore)
            for site_reading in site_readings
        ]

        # Commit the records to the database
        self.commit_records(site_records, on_conflict="overwrite", table=BreatheReading)

        # Commit changes
        self.logger.info(
            "Committing %s records to database table %s",
            green(len(site_readings)),
            green(BreatheReading.__tablename__),
        )

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        self.update_site_list_table()
        self.update_reading_table()

    