"""
Timestamp conversion functions
"""
import datetime
import pytz


def safe_strptime(naive_string, format_str):
    """Wrapper around strptime to allow for broken time strings"""
    try:
        return datetime.datetime.strptime(naive_string, format_str)
    except ValueError:
        if naive_string[11:19] == "24:00:00":
            naive_string = naive_string[:11] + "23:59:59"
            return datetime.datetime.strptime(naive_string, format_str) + datetime.timedelta(seconds=1)
    raise ValueError("Time data '{}' does not match format '{}'".format(naive_string, format_str))


def datetime_from_str(naive_string, timezone, rounded=False):
    """Convert naive string to localised datetime"""
    local_tz = pytz.timezone(timezone)
    timestamp_naive = safe_strptime(naive_string, r"%Y-%m-%d %H:%M:%S")
    if rounded:
        timestamp_naive = to_nearest_hour(timestamp_naive)
    timestamp_aware = local_tz.localize(timestamp_naive)
    return timestamp_aware


def utcstr_from_unix(timestamp):
    """Convert unix timestamp to UTC string"""
    return datetime.datetime.fromtimestamp(timestamp, pytz.utc).strftime(r"%Y-%m-%d %H:%M:%S")


def utcstr_from_datetime(timestamp):
    """Convert datetime to UTC string"""
    return timestamp.astimezone(pytz.utc).strftime(r"%Y-%m-%d %H:%M:%S")


def unix_from_str(naive_string, timezone, rounded=False):
    """Convert naive string to unix timestamp"""
    return datetime_from_str(naive_string, timezone, rounded).timestamp()


def to_nearest_hour(input_datetime):
    """Rounds to nearest hour by adding a timedelta of one hour if the minute is 30 or later then truncating on hour"""
    if input_datetime.minute >= 30:
        input_datetime += datetime.timedelta(hours=1)
    return input_datetime.replace(second=0, microsecond=0, minute=0)

