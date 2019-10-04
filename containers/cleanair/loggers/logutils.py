"""
Useful logging utilities
"""


def duration(start_time, end_time):
    """Get a human-readable duration from a start and end time in seconds"""
    seconds = int(end_time - start_time)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "%dd%dh%dm%ds" % (days, hours, minutes, seconds)
    if hours > 0:
        return "%dh%dm%ds" % (hours, minutes, seconds)
    if minutes > 0:
        return "%dm%ds" % (minutes, seconds)
    return "%ds" % (seconds,)
