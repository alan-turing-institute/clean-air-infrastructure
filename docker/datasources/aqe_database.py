"""
Get data from the AQE network via the API
"""
import csv
import io
from xml.dom import minidom
import requests
from .databases import Updater, aqe_tables
from .loggers import green


class AQEDatabase(Updater):
    """Manage interactions with the AQE database on Azure"""
    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Ensure that tables exist
        aqe_tables.initialise(self.dbcnxn.engine)

    def request_site_entries(self):
        """
        Request all laqn sites
        Remove any that do not have an opening date
        """
        try:
            endpoint = "http://acer.aeat.com/gla-cleaner-air/api/v1/gla-cleaner-air/v1/site"
            raw_data = self.api.get_response(endpoint, timeout=5.0).content
            dom = minidom.parse(io.BytesIO(raw_data))
            # Convert DOM object to a list of dictionaries. Each dictionary is an site containing site information
            return [dict(s.attributes.items()) for s in dom.getElementsByTagName("Site")]
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed: %s", endpoint, error)
            return None
        except (TypeError, KeyError):
            return None

    def request_site_readings(self, start_date, end_date, site_code):
        """
        Request all readings for {site_code} between {start_date} and {end_date}
        Remove duplicates and add the site_code
        """
        try:
            endpoint = "http://acer.aeat.com/gla-cleaner-air/api/v1/gla-cleaner-air/v1/site/{}/{}/{}".format(
                site_code, str(start_date), str(end_date)
            )
            raw_data = self.api.get_response(endpoint, timeout=5.0).content
            # Process CSV data
            csvreader = csv.reader(io.StringIO(raw_data.decode()))
            # Extract species names from the column headers
            header = csvreader.__next__()
            species = [s.split(": ")[1].split(" ")[0] for s in header[1:]]
            # Process the readings which are in the format: Date, Species1, Species2, ...
            processed_readings = []
            for reading in csvreader:
                for species_code, value in zip(species, reading[1:]):
                    processed_readings.append({"@SiteCode": site_code,
                                               "@SpeciesCode": species_code,
                                               "@MeasurementDateGMT": reading[0],
                                               "@Value": value})
            return processed_readings
        except (TypeError, KeyError):
            return None

    def update_site_list_table(self):
        """
        Update the aqe_site table
        """
        self.logger.info("Starting AQE site list update...")

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Reload site information and update the database accordingly
            self.logger.info("Requesting site info from %s", green("aeat.com API"))
            site_entries = [aqe_tables.build_site_entry(site) for site in self.request_site_entries()]
            self.logger.info("Updating site info database records")
            session.add_all(site_entries)
            self.logger.info("Committing changes to database table %s", green(aqe_tables.AQESite.__tablename__))
            session.commit()

    def update_reading_table(self):
        """"Update the database with new sensor readings."""
        self.logger.info("Starting AQE readings update...")

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Load readings for all sites and update the database accordingly
            site_info_query = session.query(aqe_tables.AQESite)
            self.logger.info("Requesting readings from %s for %s sites",
                             green("aeat.com API"), green(len(list(site_info_query))))

            # Get all readings for each site between its start and end dates and update the database
            site_readings = self.get_readings_by_site(site_info_query)
            session.add_all([aqe_tables.build_reading_entry(site_reading) for site_reading in site_readings])

            # Commit changes
            self.logger.info("Committing changes to database table %s", green(aqe_tables.AQEReading.__tablename__))
            session.commit()
