"""
Timestamp conversion functions
"""
from contextlib import suppress
from datetime import date, datetime, timedelta
from typing import Any, Union
from dateutil import parser
import pytz

TIMESTRINGS = [
    "now",
    "lasthour",
    "yesterday",
    "today",
    "tomorrow",
    "overmorrow",
    "thirdmorrow",
]


def as_datetime(maybe_dt: Any) -> datetime:
    """Convert an input that might be a datetime into a datetime"""
    # If we have a date or datetime then convert to a datetime
    if isinstance(maybe_dt, datetime):
        return maybe_dt
    if isinstance(maybe_dt, date):
        return datetime.combine(maybe_dt, datetime.min.time())
    # Attempt to parse a word into a datetime
    with suppress(ValueError):
        return datetime_from_word(maybe_dt)
    # Otherwise attempt to parse as an ISO string
    try:
        return parser.isoparse(maybe_dt)
    except ValueError:
        raise ValueError(f"Could not convert {maybe_dt} into a datetime.")


def safe_strptime(naive_string: str, format_str: str) -> datetime:
    """Wrapper around strptime to allow for broken time strings"""
    try:
        return datetime.strptime(naive_string, format_str)
    except ValueError:
        if naive_string[11:19] == "24:00:00":
            naive_string = naive_string[:11] + "23:59:59"
            return datetime.strptime(naive_string, format_str) + timedelta(seconds=1)
    raise ValueError(
        "Time data '{}' does not match format '{}'".format(naive_string, format_str)
    )


def datetime_from_str(
    naive_string: str, timezone: str, rounded: bool = False
) -> datetime:
    """Convert naive string to localised datetime"""
    local_tz = pytz.timezone(timezone)
    datetime_naive = safe_strptime(naive_string, r"%Y-%m-%d %H:%M:%S")
    if rounded:
        datetime_naive = to_nearest_hour(datetime_naive)
    datetime_aware = local_tz.localize(datetime_naive)
    return datetime_aware


def datetime_from_unix(timestamp: Union[str, int]) -> datetime:
    """Convert unix timestamp to datetime"""
    return datetime.fromtimestamp(timestamp, pytz.utc)


def utcstr_from_unix(timestamp: Union[str, int], rounded: bool = False) -> str:
    """Convert unix timestamp to UTC string"""
    datetime_aware = datetime_from_unix(timestamp)
    if rounded:
        datetime_aware = to_nearest_hour(datetime_aware)
    return datetime_aware.strftime(r"%Y-%m-%d %H:%M:%S")


def utcstr_from_datetime(input_datetime: datetime, rounded: bool = False) -> str:
    """Convert datetime to UTC string"""
    datetime_aware = input_datetime.astimezone(pytz.utc)
    if rounded:
        datetime_aware = to_nearest_hour(datetime_aware)
    return datetime_aware.strftime(r"%Y-%m-%d %H:%M:%S")


def unix_from_str(naive_string: str, timezone: str, rounded: bool = False) -> datetime:
    """Convert naive string to unix timestamp"""
    return datetime_from_str(naive_string, timezone, rounded).timestamp()


def to_nearest_hour(input_datetime: datetime) -> datetime:
    """Rounds to nearest hour by adding a timedelta of one hour if the minute is 30 or later then truncating on hour"""
    if input_datetime.minute >= 30:
        input_datetime += timedelta(hours=1)
    return input_datetime.replace(minute=0, second=0, microsecond=0)


def datetime_from_word(timestring: str) -> datetime:
    """Convert one of a set of known meaningful words to a datetime"""
    if timestring in TIMESTRINGS:
        # Hour-based strings (truncated to hour)
        if timestring == "now":
            output_dt = datetime.now().replace(microsecond=0, second=0, minute=0)

        elif timestring == "lasthour":
            output_dt = (datetime.now() - timedelta(hours=1)).replace(
                microsecond=0, second=0, minute=0
            )

        # Day-based strings (truncated to midnight)
        elif timestring == "yesterday":
            output_dt = datetime.combine(
                date.today() - timedelta(days=1), datetime.min.time()
            )

        elif timestring == "today":
            output_dt = datetime.combine(date.today(), datetime.min.time())

        elif timestring == "tomorrow":
            output_dt = datetime.combine(
                date.today() + timedelta(days=1), datetime.min.time()
            )

        elif timestring == "overmorrow":
            output_dt = datetime.combine(
                date.today() + timedelta(days=2), datetime.min.time()
            )

        elif timestring == "thirdmorrow":
            output_dt = datetime.combine(
                date.today() + timedelta(days=3), datetime.min.time()
            )

        return output_dt

    raise ValueError(f"{timestring} is not a valid time description")
