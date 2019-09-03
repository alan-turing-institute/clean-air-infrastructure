"""
Get data from the LAQN network via the API maintained by Kings College London:
  (https://www.londonair.org.uk/Londonair/API/)
"""
import requests
from .databases import Updater, laqn_tables
from .loggers import green
from .apis import APIReader


class LAQNDatabase(Updater, APIReader):
    def __init__(self, *args, **kwargs):
        # Initialise the base classes
        super().__init__(*args, **kwargs)

        # Ensure that tables exist
        laqn_tables.initialise(self.dbcnxn.engine)

    def request_site_entries(self):
        """
        Request all LAQN sites
        Remove any that do not have an opening date
        """
        try:
            endpoint = "http://api.erg.kcl.ac.uk/AirQuality/Information/MonitoringSites/GroupName=London/Json"
            raw_data = self.get_response(endpoint, timeout=5.0).json()["Sites"]["Site"]
            # Remove sites with no opening date
            processed_data = [site for site in raw_data if site['@DateOpened']]
            if len(processed_data) != len(raw_data):
                self.logger.warning("Excluded %i site(s) with no opening date from the database",
                                    len(raw_data) - len(processed_data))
            return processed_data
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
            endpoint = "http://api.erg.kcl.ac.uk/AirQuality/Data/Site/SiteCode={}/StartDate={}/EndDate={}/Json".format(
                site_code, str(start_date.date()), str(end_date.date())
            )
            raw_data = self.get_response(endpoint, timeout=5.0).json()["AirQualityData"]["Data"]
            # Drop duplicates
            processed_data = [dict(t) for t in {tuple(d.items()) for d in raw_data}]
            # Add the site_code
            for reading in processed_data:
                reading["@SiteCode"] = site_code
            return processed_data
        except requests.exceptions.HTTPError as error:
            self.logger.warning("Request to %s failed:", endpoint)
            self.logger.warning(error)
            return None
        except (TypeError, KeyError):
            return None

    def update_site_list_table(self):
        """
        Update the laqn_site table
        """
        self.logger.info("Starting LAQN site list update...")

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Reload site information and update the database accordingly
            self.logger.info("Requesting site info from %s", green("KCL API"))
            site_entries = [laqn_tables.build_site_entry(site) for site in self.request_site_entries()]
            self.logger.info("Updating site info database records")
            session.add_all(site_entries)
            self.logger.info("Committing changes to database table %s", green(laqn_tables.LAQNSite.__tablename__))
            session.commit()

    def update_reading_table(self):
        """Update the readings table with new sensor readings."""
        self.logger.info("Starting %s readings update...", green("LAQN"))

        # Open a DB session
        with self.dbcnxn.open_session() as session:
            # Load readings for all sites and update the database accordingly
            site_info_query = session.query(laqn_tables.LAQNSite)
            self.logger.info("Requesting readings from %s for %s sites",
                             green("KCL API"), green(len(list(site_info_query))))

            # Get all readings for each site between its start and end dates and update the database
            site_readings = self.get_readings_by_site(site_info_query, self.start_date, self.end_date)
            session.add_all([laqn_tables.build_reading_entry(site_reading) for site_reading in site_readings])

            # Commit changes
            self.logger.info("Committing %s records to database table %s",
                             green(len(site_readings)),
                             green(laqn_tables.LAQNReading.__tablename__))
            session.commit()
        self.logger.info("Finished %s readings update...", green("LAQN"))

    def update_remote_tables(self):
        """Update all relevant tables on the remote database"""
        self.update_site_list_table()
        self.update_reading_table()
