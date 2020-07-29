"""
Timestamp conversion functions
"""

from typing import Union
import datetime
from dateutil import parser
import pytz


def as_datetime(maybe_dt: Union[datetime.datetime, datetime.date, str]) -> datetime.datetime:
    """Convert an input that might be a datetime into a datetime"""
    # Return if already a datetime
    if isinstance(maybe_dt, datetime.datetime):
        return maybe_dt
    # Convert date to datetime
    if isinstance(maybe_dt, datetime.date):
        return datetime.datetime.combine(maybe_dt, datetime.datetime.min.time())
    # Convert strings into a datetime
    if maybe_dt == "now":
        return datetime.datetime.now().replace(microsecond=0, second=0, minute=0)
    if maybe_dt == "lasthour":
        return (datetime.datetime.now() - datetime.timedelta(hours=1)).replace(
            microsecond=0, second=0, minute=0
        )
    if maybe_dt == "today":
        return datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())

    if maybe_dt == "tomorrow":
        return datetime.datetime.combine(
            datetime.date.today() + datetime.timedelta(days=1), datetime.datetime.min.time()
        )

    if maybe_dt == "yesterday":
        return datetime.datetime.combine(
            datetime.date.today() - datetime.timedelta(days=1), datetime.datetime.min.time()
        )

    return parser.isoparse(maybe_dt)


def safe_strptime(naive_string, format_str):
    """Wrapper around strptime to allow for broken time strings"""
    try:
        return datetime.datetime.strptime(naive_string, format_str)
    except ValueError:
        if naive_string[11:19] == "24:00:00":
            naive_string = naive_string[:11] + "23:59:59"
            return datetime.datetime.strptime(
                naive_string, format_str
            ) + datetime.timedelta(seconds=1)
    raise ValueError(
        "Time data '{}' does not match format '{}'".format(naive_string, format_str)
    )


def datetime_from_str(naive_string, timezone, rounded=False):
    """Convert naive string to localised datetime"""
    local_tz = pytz.timezone(timezone)
    datetime_naive = safe_strptime(naive_string, r"%Y-%m-%d %H:%M:%S")
    if rounded:
        datetime_naive = to_nearest_hour(datetime_naive)
    datetime_aware = local_tz.localize(datetime_naive)
    return datetime_aware


def datetime_from_unix(timestamp):
    """Convert unix timestamp to datetime"""
    return datetime.datetime.fromtimestamp(timestamp, pytz.utc)


def utcstr_from_unix(timestamp, rounded=False):
    """Convert unix timestamp to UTC string"""
    datetime_aware = datetime_from_unix(timestamp)
    if rounded:
        datetime_aware = to_nearest_hour(datetime_aware)
    return datetime_aware.strftime(r"%Y-%m-%d %H:%M:%S")


def utcstr_from_datetime(input_datetime, rounded=False):
    """Convert datetime to UTC string"""
    datetime_aware = input_datetime.astimezone(pytz.utc)
    if rounded:
        datetime_aware = to_nearest_hour(datetime_aware)
    return datetime_aware.strftime(r"%Y-%m-%d %H:%M:%S")


def unix_from_str(naive_string, timezone, rounded=False):
    """Convert naive string to unix timestamp"""
    return datetime_from_str(naive_string, timezone, rounded).timestamp()


def to_nearest_hour(input_datetime):
    """Rounds to nearest hour by adding a timedelta of one hour if the minute is 30 or later then truncating on hour"""
    if input_datetime.minute >= 30:
        input_datetime += datetime.timedelta(hours=1)
    return input_datetime.replace(minute=0, second=0, microsecond=0)
