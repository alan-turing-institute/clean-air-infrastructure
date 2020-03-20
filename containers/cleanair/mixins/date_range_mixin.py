"""
Mixin for classes that need to keep track of date ranges
"""
import datetime
import dateutil
from ..loggers import get_logger


class DateRangeMixin:
    """Manage data ranges"""

    def __init__(self, end, ndays, **kwargs):
        """Returns a start_date, start_datetime, end_date and end_datetime
        
        Parameters
        ___
        end: datetime or str
        ndays: Number of days to offset end_date to calculate start_date and start_datetime
        Returns:
            now: end_date is today. end_datetime is the time now minus 1 hour 
            today: end_date is today. end_datetime is today at midnight
            datetime.date: end_date is the date passed. end_datetime is the date passed at midnight
            datetime.datetime: end_date is the date of the datetime passed. end_datetime is the datetime passed
            str (iso format): 
                If the string contains a time:
                    end_date is the date of the parsed iso string. end_datetime is the datetime of the parsed iso string.
                If the string only contains a date:
                    end_date is the date of the parsed iso string. end_datetime is midnight
    """

        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Set the date range
        if end == "now":
            self.end_datetime = (
                datetime.datetime.now() - datetime.timedelta(hours=1)
            ).replace(microsecond=0, second=0, minute=0)
            self.end_date = self.end_datetime.date()
        elif end == "today":
            self.end_date = datetime.datetime.today().date()
            self.end_datetime = self.midnight(self.end_date)

        elif end == "yesterday":
            self.end_date = (
                datetime.datetime.today() - datetime.timedelta(days=1)
            ).date()
            self.end_datetime = self.midnight(self.end_date)

        elif isinstance(end, datetime.date):
            self.end_date = end
            self.end_datetime = self.midnight(self.end_date)

        elif isinstance(end, datetime.datetime):
            self.end_datetime = end
            self.end_date = end.date()

        elif isinstance(end, str):

            end_date_parsed = dateutil.parser.parse(end, dayfirst=False)

            if self.is_date(end_date_parsed):
                # If end_date has a time of T00:00:00
                self.end_date = end_date_parsed.date()
                self.end_datetime = self.midnight(self.end_date)

            else:
                # If end_date has a time other than T00:00:00
                self.end_datetime = end_date_parsed
                self.end_date = end_date_parsed.date()

        else:
            raise ValueError("Argument end was not valid")

        self.start_date = self.end_date - datetime.timedelta(days=ndays)
        self.start_datetime = self.end_datetime - datetime.timedelta(days=ndays)

        print(self.start_date, self.start_datetime, self.end_date, self.end_datetime)

    def is_date(self, datetime_):
        "Check if self.end_date is on the hour (a date)"

        is_zero_hour_min = self.midnight(datetime_) == datetime_

        return is_zero_hour_min

    @staticmethod
    def midnight(date_):

        return datetime.datetime.combine(date_, datetime.datetime.min.time())
