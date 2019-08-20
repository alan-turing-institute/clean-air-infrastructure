import datetime
import requests
from ..loggers import get_logger, bold


class APIReader():
    """Manage interactions with an external API"""
    def __init__(self, end = 'today', ndays = 2, **kwargs):
        # Set up logging
        self.logger = get_logger(__name__, kwargs.get("verbose", 0))

        # Set the date range
        if end == "today":
            self.end_date = datetime.datetime.today().date()
        else:
            self.end_date = datetime.datetime.strptime(end, r"%Y-%m-%d").date()
        self.start_date = self.end_date - datetime.timedelta(days=(ndays - 1))
        self.start_time = "00:00:00"
        self.end_time = "23:59:59"

        # Log an introductory message
        self.logger.info("Requesting data between the following times:")
        self.logger.info("... %s on %s", bold(self.start_time), bold(self.start_date))
        self.logger.info("... %s on %s", bold(self.end_time), bold(self.end_date))

    def get_available_datetimes(self, site):
        """
        Get the dates that data is available for a site between start_date and end_date
        If no data is available between these dates returns None
        """
        # Load start dates
        start_dates = [self.start_date]
        if site.DateOpened:
            start_dates.append(site.DateOpened.date())

        # Load end dates
        end_dates = [self.end_date]
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
