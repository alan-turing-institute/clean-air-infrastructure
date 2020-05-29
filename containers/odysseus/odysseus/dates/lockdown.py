"""Functions and constants for the lockdown period."""

LOCKDOWN_BASELINE_START = "2020-03-30"
LOCKDOWN_BASELINE_END = "2020-04-20"


def timestamp_is_lockdown(timestamp: str) -> bool:
    """
    Check if the timestamp is in the lockdown period.

    Args:
        timestamp: The date(time) to check.

    Returns:
        True if the timestamp is greater than or equal to the lockdown start
        and strictly less than the lockdown end.
    """
    return LOCKDOWN_BASELINE_START <= timestamp < LOCKDOWN_BASELINE_END
