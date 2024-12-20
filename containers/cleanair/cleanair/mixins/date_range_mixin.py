"""
Mixin for classes that need to keep track of date ranges
"""
from itertools import product
from datetime import datetime, timedelta
from dateutil.rrule import rrule
from dateutil.parser import isoparse
from ..loggers import get_logger
from ..timestamps import as_datetime


class DateRangeMixin:
    """Manage data ranges"""

    def __init__(self, end, nhours, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Convert end argument into a datetime
        self.end_datetime = as_datetime(end)

        # Construct the start datetime using nhours
        self.start_datetime = self.end_datetime - timedelta(hours=nhours)

        # Construct start and end dates, which might be useful
        self.start_date = self.start_datetime.date()
        self.end_date = self.end_datetime.date()


class DateGeneratorMixin:
    """Generate date ranges"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @staticmethod
    def get_datetime_list(start_datetime, end_datetime, frequency):
        """
        Get a list of datetimes between start_datetime and end_datetime (exclusive)

        Args:
            start_datetime (str): isostring specifying start datetime
            end_datetime (str): isostring specifying end datetime. The last datetime is less than this value
            frequency (int): An integer specifying the frequency. Use dateutil.rrule.HOURLY, dateutil.rrule.DAILY etc

        Returns:
            list[str]: A list of iso datetimes
        """

        return list(
            map(
                datetime.isoformat,
                rrule(
                    freq=frequency,
                    dtstart=isoparse(start_datetime),
                    until=isoparse(end_datetime),
                ),
            )
        )[:-1]

    def get_arg_list(
        self, start_datetime, end_datetime, frequency, *args, transpose=True
    ):
        """
        Get the cartesian product of datetime_list and *args where args are iterables
        to be used as inputs for functions which need to operate over times and other arguments


        Args:
            datetime_list (list[str]): List of datetime strings. Can generate with self.get_datetime_list
            *args (iterable): iterable arguments to create product with
            transpose (bool): Default False. Transpose the output to allow use with map()
        """

        arg_gen = product(
            self.get_datetime_list(start_datetime, end_datetime, frequency), *args
        )

        if transpose:
            return zip(*arg_gen)

        return arg_gen
