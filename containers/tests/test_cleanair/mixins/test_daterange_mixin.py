"""Daterange mixin  tests"""
from cleanair.mixins import DateRangeMixin
# pylint: skip-file
from dateutil.parser import isoparse


class ExampleDateRangeClass(DateRangeMixin):
    """An example class using a daterange mixin"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)


def test_daterange_mixin():
    "Test daterange mixin"
    date_instance = ExampleDateRangeClass(end="2020-01-02", nhours=5)

    assert date_instance.end_date == isoparse("2020-01-02").date()
    assert date_instance.end_datetime == isoparse("2020-01-02T00:00:00")
    assert date_instance.start_date == isoparse("2020-01-01").date()
    assert date_instance.start_datetime == isoparse("2020-01-01T19:00:00")
