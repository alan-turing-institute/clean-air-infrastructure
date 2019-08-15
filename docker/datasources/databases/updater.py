from ..apis import APIReader
from .connector import Connector
from ..loggers import get_logger, green


class Updater():
    """Manage interactions with the Azure databases"""
    def __init__(self, *args, **kwargs):
        self.api = APIReader(*args, **kwargs)
        self.dbcnxn = Connector(*args, **kwargs)
        self.logger = get_logger(__name__, kwargs.get("verbose", 0))

    def get_available_readings(self, site_list_query):
        # Restrict to sites which were open during the requested time period
        site_availabilities = [self.api.get_available_datetimes(site) for site in site_list_query]
        sites_with_data = [(site, *dates) for site, dates in zip(site_list_query, site_availabilities) if dates]
        self.logger.info("%s sites have data between %s and %s",
                         green(len(sites_with_data)), green(self.api.start_date), green(self.api.end_date))

        # Get all readings for each site between its start and end dates
        site_readings = []
        for site, start_date, end_date in sites_with_data:
            self.logger.info("Attempting to download data for %s between %s and %s",
                             green(site.SiteCode), green(start_date), green(end_date))

            request = self.request_site_readings(site.SiteCode, start_date, end_date)
            if request:
                site_readings += request
        return site_readings

    def request_site_entries(self):
        """Request all sites. Remove any that do not have an opening date."""
        raise NotImplementedError("Must be implemented by child classes")

    def request_site_readings(self, site_code, start_date, end_date):
        """
        Request all readings for {site_code} between {start_date} and {end_date}.
        Remove duplicates and add the site_code.
        """
        raise NotImplementedError("Must be implemented by child classes")

    def update_site_list_table(self):
        """Update the database with new sites."""
        raise NotImplementedError("Must be implemented by child classes")

    def update_reading_table(self):
        """Update the database with new sensor readings."""
        raise NotImplementedError("Must be implemented by child classes")
