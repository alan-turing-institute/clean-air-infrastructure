"""
Mixin for classes that need to keep track of date ranges
"""
import datetime
import dateutil
from ..loggers import get_logger


class DateRangeMixin:
    """Manage data ranges"""

    def __init__(self, end, ndays, **kwargs):
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
            self.start_datetime = self.end_datetime - datetime.timedelta(days=(ndays))
        else:
            if end == "today":
                self.end_date = datetime.datetime.today().date()
            elif end == "yesterday":
                self.end_date = (
                    datetime.datetime.today() - datetime.timedelta(days=1)
                ).date()

            else:
                if isinstance(end, datetime.date):
                    self.end_date = end
                if isinstance(end, datetime.datetime):
                    self.end_date = end.date()
                else:

                    end_date = dateutil.parser.parse(end, dayfirst=False)

                    if not self.is_date(end_date):
                        # If end_date has a time other than T00:00:00
                        self.end_datetime = end_date
                        self.end_date = end_date.date()
                        self.start_datetime = self.end_datetime - datetime.timedelta(
                            days=(ndays - 1)
                        )
                        self.start_date = self.end_date - datetime.timedelta(
                            days=(ndays - 1)
                        )
                    else:
                        # If end_date has a time of T00:00:00
                        self.end_date = end_date.date()
                        self.start_date = end_date - datetime.timedelta(
                            days=(ndays - 1)
                        )
                        self.start_datetime, self.end_datetime = self.get_datetimes(
                            self.start_date, self.end_date
                        )

    @staticmethod
    def is_date(datetime_):
        "Check if self.end_date is on the hour (a date) or a datetime"

        is_zero_hour_min = (
            datetime.datetime.combine(datetime_.date(), datetime.datetime.min.time())
            == datetime_
        )

        return is_zero_hour_min

    @staticmethod
    def get_datetimes(start_date, end_date):
        """Get min and max datetimes between start_date and end_date"""

        start_datetime = datetime.datetime.combine(
            start_date, datetime.datetime.min.time()
        )
        end_datetime = datetime.datetime.combine(end_date, datetime.datetime.max.time())

        return start_datetime, end_datetime
