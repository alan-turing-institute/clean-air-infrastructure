"""
Get data from the LAQN network via the API maintained by Kings College London:
  (https://www.londonair.org.uk/Londonair/API/)
"""
import requests
from .databases import Updater, scoot_tables
from .loggers import green


class ScootDatabase(Updater):
    def __init__(self, *args, **kwargs):
        # Initialise the base class
        super().__init__(*args, **kwargs)

        # Ensure that tables exist
        scoot_tables.initialise(self.dbcnxn.engine)

    def request_site_entries(self):
        """
        Request all Scoot sites
        Remove any that do not have an opening date
        """
        # try:
        #     endpoint = "http://api.erg.kcl.ac.uk/AirQuality/Information/MonitoringSites/GroupName=London/Json"
        #     raw_data = self.api.get_response(endpoint, timeout=5.0).json()["Sites"]["Site"]
        #     # Remove sites with no opening date
        #     processed_data = [site for site in raw_data if site['@DateOpened']]
        #     if len(processed_data) != len(raw_data):
        #         self.logger.warning("Excluded %i sites which do not have an opening date from the database",
        #                             len(raw_data) - len(processed_data))
        #     return processed_data
        # except requests.exceptions.HTTPError as error:
        #     self.logger.warning("Request to %s failed: %s", endpoint, error)
        #     return None
        # except (TypeError, KeyError):
        #     return None
        pass

    def request_site_readings(self, site_code, start_date, end_date):
        """
        Request all readings for {site_code} between {start_date} and {end_date}
        Remove duplicates and add the site_code
        """
        # try:
        #     endpoint = "http://api.erg.kcl.ac.uk/AirQuality/Data/Site/SiteCode={}/StartDate={}/EndDate={}/Json".format(
        #         site_code, str(start_date.date()), str(end_date.date())
        #     )
        #     raw_data = self.api.get_response(endpoint, timeout=5.0).json()["AirQualityData"]["Data"]
        #     # Drop duplicates
        #     processed_data = [dict(t) for t in {tuple(d.items()) for d in raw_data}]
        #     # Add the site_code
        #     for reading in processed_data:
        #         reading["@SiteCode"] = site_code
        #     return processed_data
        # except (requests.exceptions.HTTPError) as e:
        #     self.logger.warning("Request to %s failed: %s", endpoint, e)
        #     return None
        # except (TypeError, KeyError):
        #     return None
        pass

    def update_site_list_table(self):
        """
        Update the laqn_site table
        """
        self.logger.info("Starting Scoot site list update...")

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Reload site information and update the database accordingly
            self.logger.info("Requesting site info from %s", green("TfL API"))
            site_entries = [scoot_tables.build_site_entry(site) for site in self.request_site_entries()]
            self.logger.info("Updating site info database records")
            session.add_all(site_entries)
            self.logger.info("Committing changes to database table %s", green(scoot_tables.ScootSite.__tablename__))
            session.commit()

    def update_reading_table(self):
        """Update the database with new traffic data."""
        self.logger.info("Starting Scoot data update...")

        # # Open a DB session
        # with self.dbcnxn.open_session() as session:
        #     # Load readings for all sites and update the database accordingly
        #     site_info_query = session.query(scoot_tables.ScootSite)
        #     self.logger.info("Requesting readings from %s for %s sites",
        #                      green("KCL API"), green(len(list(site_info_query))))

        #     # Get all readings for each site between its start and end dates and update the database
        #     site_readings = self.get_available_readings(site_info_query)
        #     session.add_all([scoot_tables.build_reading_entry(site_reading) for site_reading in site_readings])

        #     # Commit changes
        #     self.logger.info("Committing changes to database table %s", green(scoot_tables.ScootReading.__tablename__))
        #     session.commit()
