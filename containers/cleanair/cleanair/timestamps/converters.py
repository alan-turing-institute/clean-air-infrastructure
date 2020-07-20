"""
Timestamp conversion functions
"""
from datetime import date, datetime, timedelta
from dateutil import parser
import pytz


def as_datetime(maybe_dt):
    """Convert an input that might be a datetime into a datetime"""
    if isinstance(maybe_dt, datetime):
        return maybe_dt
    if isinstance(maybe_dt, date):
        return datetime.combine(maybe_dt, datetime.min.time())
    return parser.isoparse(maybe_dt)


def safe_strptime(naive_string, format_str):
    """Wrapper around strptime to allow for broken time strings"""
    try:
        return datetime.strptime(naive_string, format_str)
    except ValueError:
        if naive_string[11:19] == "24:00:00":
            naive_string = naive_string[:11] + "23:59:59"
            return datetime.strptime(naive_string, format_str) + datetime.timedelta(
                seconds=1
            )
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
    return datetime.fromtimestamp(timestamp, pytz.utc)


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


def day_to_iso(day: str) -> str:
    """Convert one of 'now', 'lasthour', 'today', 'tomorrow' or 'yesterday' to a iso string"""

    # Convert end argument into a datetime
    if day == "now":
        return datetime.now().replace(microsecond=0, second=0, minute=0).isoformat()
    if day == "lasthour":
        return (
            (datetime.now() - timedelta(hours=1))
            .replace(microsecond=0, second=0, minute=0)
            .isoformat()
        )
    if day == "today":
        return datetime.combine(date.today(), datetime.min.time()).isoformat()

    if day == "tomorrow":
        return datetime.combine(
            date.today() + timedelta(days=1), datetime.min.time()
        ).isoformat()

    if day == "yesterday":
        return datetime.combine(
            date.today() - timedelta(days=1), datetime.min.time()
        ).isoformat()

    raise ValueError(f"{day} is not a valid day")
