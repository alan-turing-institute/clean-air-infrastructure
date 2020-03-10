"""
Mixin for classes that need to keep track of date ranges
"""
from datetime import date, datetime, timedelta
import dateutil
from ..loggers import get_logger


class DateRangeMixin:
    """Manage data ranges"""

    def __init__(self, end, nhours, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Convert end argument into a datetime
        if end == "now":
            self.end_datetime = datetime.now().replace(
                microsecond=0, second=0, minute=0
            )
        if end == "lasthour":
            self.end_datetime = (datetime.now() - timedelta(hours=1)).replace(
                microsecond=0, second=0, minute=0
            )
        elif end == "today":
            self.end_datetime = datetime.combine(date.today(), datetime.min.time())
        elif end == "yesterday":
            self.end_datetime = datetime.combine(
                date.today() - timedelta(days=1), datetime.min.time()
            )
        else:
            if isinstance(end, date):
                self.end_datetime = datetime.combine(end, datetime.min.time())
            if isinstance(end, datetime):
                self.end_datetime = end
            else:
                self.end_datetime = dateutil.parser.parse(end, dayfirst=True)

        # Construct the start datetime using nhours
        self.start_datetime = self.end_datetime - timedelta(hours=nhours)

        # Construct start and end dates, which might be useful
        self.start_date = self.start_datetime.date()
        self.end_date = self.end_datetime.date()
