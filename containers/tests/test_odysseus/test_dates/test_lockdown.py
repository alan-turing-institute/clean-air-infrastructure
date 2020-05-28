"""Test dates are within the lockdown period."""

from datetime import datetime, timedelta
from odysseus.dates import (
    timestamp_is_lockdown,
    LOCKDOWN_BASELINE_START,
    LOCKDOWN_BASELINE_END,
)
from .date_formats import SIMPLE, LONG, LONGT


def test_timestamp_is_lockdown():
    """Test the timestamp_is_lockdown method."""
    lockdown_start = datetime.strptime(LOCKDOWN_BASELINE_START, SIMPLE)
    lockdown_end = datetime.strptime(LOCKDOWN_BASELINE_END, SIMPLE)

    # check the start date always returns true
    assert timestamp_is_lockdown(lockdown_start.strftime(SIMPLE))
    assert timestamp_is_lockdown(lockdown_start.strftime(LONG))
    assert timestamp_is_lockdown(lockdown_start.strftime(LONGT))

    # check the end date always returns false
    assert not timestamp_is_lockdown(lockdown_end.strftime(SIMPLE))
    assert not timestamp_is_lockdown(lockdown_end.strftime(LONG))
    assert not timestamp_is_lockdown(lockdown_end.strftime(LONGT))

    # check dates before lockdown return false
    before_lockdown = lockdown_start + timedelta(days=-1)
    assert not timestamp_is_lockdown(before_lockdown.strftime(SIMPLE))
    assert not timestamp_is_lockdown(before_lockdown.strftime(LONG))
    assert not timestamp_is_lockdown(before_lockdown.strftime(LONGT))

    # check dates during lockdown return true
    during_lockdown = lockdown_end + timedelta(days=-1)
    assert timestamp_is_lockdown(during_lockdown.strftime(SIMPLE))
    assert timestamp_is_lockdown(during_lockdown.strftime(LONG))
    assert timestamp_is_lockdown(during_lockdown.strftime(LONGT))
