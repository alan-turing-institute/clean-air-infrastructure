"""Functions and constants for the normal baseline period."""

NORMAL_BASELINE_START = "2020-02-10"
NORMAL_BASELINE_END = "2020-03-02"


def timestamp_is_normal(timestamp: str) -> bool:
    """
    Check if the timestamp is in the normal period.

    Args:
        timestamp: The date(time) to check.

    Returns:
        True if the timestamp is greater than or equal to the normal start
        and strictly less than the normal end.
    """
    return NORMAL_BASELINE_START <= timestamp < NORMAL_BASELINE_END
