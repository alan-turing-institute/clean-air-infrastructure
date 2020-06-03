"""date parsers for api webargs"""
from datetime import datetime
from dateutil.parser import isoparse
from webargs import ValidationError


def validate_iso_string(iso_datestring):
    """Ensure iso_datestring can be parsed"""
    try:
        isoparse(iso_datestring)
    except:
        raise ValidationError("Not a valid iso date")


def validate_today_or_before(iso_datestring):
    """Check iso_datestring is today or before"""

    validate_iso_string(iso_datestring)

    if isoparse(iso_datestring).date() > datetime.today().date():
        raise ValidationError("Dates in the future cannot be requested")


def validate_lockdown_date(iso_datestring, lockdown_baseline_end_date):
    """Check iso_datestring is today or before and is after lockdown_baseline_end_date"""
    validate_today_or_before(iso_datestring)

    if isoparse(iso_datestring) < isoparse(lockdown_baseline_end_date):
        raise ValidationError("Cannot be before the baseline end date")
