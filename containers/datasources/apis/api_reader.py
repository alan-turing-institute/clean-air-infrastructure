import datetime
import requests
from ..loggers import get_logger, green


class APIReader():
    """Manage interactions with an external API"""
    def __init__(self, **kwargs):
        # Set up logging
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__, kwargs.get("verbose", 0))

    def get_readings_by_site(self, site_list_query, start_date, end_date):
        # Restrict to sites which were open during the requested time period
        site_dates = [self.get_available_datetimes(site, start_date, end_date) for site in site_list_query]
        available_sites = [(s, *[d.date() for d in dates]) for s, dates in zip(site_list_query, site_dates) if dates]
        self.logger.info("%s sites have data between %s and %s",
                         green(len(available_sites)), green(start_date), green(end_date))

        # Get all readings for each site between its start and end dates
        site_readings = []
        for site, available_start_date, available_end_date in available_sites:
            self.logger.info("Attempting to download data for %s between %s and %s",
                             green(site.SiteCode), green(available_start_date), green(available_end_date))
            response = self.request_site_readings(available_start_date, available_end_date, site_code=site.SiteCode)
            if response:
                site_readings += response
        return site_readings

    def request_site_readings(self, start_date, end_date, site_code):
        """
        Request all readings between {start_date} and {end_date}, removing duplicates.
        """
        raise NotImplementedError("Must be implemented by child classes")

    @staticmethod
    def get_available_datetimes(site, start_date, end_date):
        """
        Get the dates that data is available for a site between start_date and end_date
        If no data is available between these dates returns None
        """
        # Load start dates
        start_dates = [start_date]
        if site.DateOpened:
            start_dates.append(site.DateOpened.date())

        # Load end dates
        end_dates = [end_date]
        if site.DateClosed:
            end_dates.append(site.DateClosed.date())

        # Start on requested/opening date (whichever is later)
        # End on requested/closing date (whichever is earlier)
        available_dates = [max(start_dates), min(end_dates)]

        # If the start date is after the end date then return None
        if available_dates[0] >= available_dates[1]:
            return None

        # Convert these to datetimes by setting the timestamp to midnight at the start of the day
        return list(map(lambda d: datetime.datetime.combine(d, datetime.datetime.min.time()), available_dates))

    @staticmethod
    def get_response(api_endpoint, timeout=60.0):
        """Return the response from an API"""
        response = requests.get(api_endpoint, timeout=timeout)
        response.raise_for_status()
        return response
