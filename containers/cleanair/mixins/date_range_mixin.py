"""
Mixin for classes that need to keep track of date ranges
"""
import datetime
from ..loggers import get_logger, green


class DateRangeMixin:
    """Manage data ranges"""

    def __init__(self, end, ndays, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Set the date range
        if end == "today":
            self.end_date = datetime.datetime.today().date()
        elif end == "yesterday":
            self.end_date = (
                datetime.datetime.today() - datetime.timedelta(days=1)
            ).date()
        else:
            self.end_date = datetime.datetime.strptime(end, r"%Y-%m-%d").date()
        self.start_date = self.end_date - datetime.timedelta(days=(ndays - 1))

        # Set the time range
        self.start_datetime, self.end_datetime = self.get_datetimes(
            self.start_date, self.end_date
        )

        # Log an introductory message
        self.logger.info("Requesting data between the following time points:")
        self.logger.info(
            "... %s and %s", green(self.start_datetime), green(self.end_datetime)
        )

    @staticmethod
    def get_datetimes(start_date, end_date):
        """Get min and max datetimes between start_date and end_date"""
        start_datetime = datetime.datetime.combine(
            start_date, datetime.datetime.min.time()
        )
        end_datetime = datetime.datetime.combine(end_date, datetime.datetime.max.time())
        return start_datetime, end_datetime
