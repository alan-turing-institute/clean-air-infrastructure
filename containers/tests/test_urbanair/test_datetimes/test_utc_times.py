"""Air quality forecast API route tests"""
from datetime import datetime
from urbanair.databases.schemas.jamcam import UTCTime
import json


class TestUTCTime:
    """Basic test to check datetimes are returned as UTC"""

    utc_time_string_good = "2020-01-01T02:00:00+00:00"
    utc_time_string_bad = "2020-01-01T02:00:00"

    utc_time_good = datetime.fromisoformat(utc_time_string_good)
    utc_time_bad = datetime.fromisoformat(utc_time_string_bad)

    def test_utctime_is_good(self):
        """Test a good datetime stamp is handled correctly"""
        utc_string = json.loads(
            UTCTime(measurement_start_utc=self.utc_time_string_good).json()
        )["measurement_start_utc"]
        assert utc_string == self.utc_time_string_good

    def test_bad_utctime_is_fixed(self):
        """Test a good datetime stamp is handled correctly"""
        utc_string = json.loads(
            UTCTime(measurement_start_utc=self.utc_time_string_bad).json()
        )["measurement_start_utc"]
        assert utc_string != self.utc_time_string_bad
        assert utc_string == self.utc_time_string_good
