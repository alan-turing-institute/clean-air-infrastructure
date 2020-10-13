"""Tests for datetime conversions"""
from datetime import date, datetime
import pytest
import pytz
from cleanair.timestamps import (
    as_datetime,
    datetime_from_word,
    datetime_from_str,
    TIMESTRINGS,
)


@pytest.mark.parametrize(
    "timestring", TIMESTRINGS,
)
def test_datetime_from_word(timestring):
    """Test the test_datetime_from_word function"""
    datetime_ = datetime_from_word(timestring)
    assert isinstance(datetime_, datetime)


@pytest.mark.parametrize("timestring", ["not", "valid", "input"])
def test_datetime_from_word_failures(timestring):
    """Test failures of the test_datetime_from_word function"""
    with pytest.raises(ValueError):
        datetime_from_word(timestring)


@pytest.mark.parametrize(
    "maybe_dt, expected",
    [
        (datetime(2020, 1, 15, 12, 15, 00), datetime(2020, 1, 15, 12, 15, 0)),
        (date(2020, 1, 15), datetime(2020, 1, 15, 0, 0, 0)),
        ("today", datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)),
        ("2020-09-29T06:15:00.000000", datetime(2020, 9, 29, 6, 15, 0)),
    ],
)
def test_as_datetime(maybe_dt, expected):
    """Test the as_datetime function"""
    assert as_datetime(maybe_dt) == expected


@pytest.mark.parametrize("maybe_dt", ["not", "valid", "input"])
def test_as_datetime_failures(maybe_dt):
    """Test failures of the as_datetime function"""
    with pytest.raises(ValueError):
        as_datetime(maybe_dt)


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("2020-09-30 24:00:00", datetime(2020, 10, 1, 0, 0, 0, tzinfo=pytz.utc)),
        ("2020-09-29 12:15:00", datetime(2020, 9, 29, 12, 15, 0, tzinfo=pytz.utc)),
    ],
)
def test_datetime_from_str(test_input, expected):
    """Test the datetime_from_str function"""
    assert datetime_from_str(test_input, timezone="UTC") == expected
