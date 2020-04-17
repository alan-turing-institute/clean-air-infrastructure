from webargs.flaskparser import use_args, use_kwargs,  abort
from dateutil.parser import isoparse
from datetime import datetime
from webargs import fields, ValidationError


def validate_iso_string(iso_datestring):

    try:
        isoparse(iso_datestring)
    except:
        raise ValidationError("Not a valid iso date")


def validate_today_or_before(iso_datestring):
    """Check a datetime is today or before"""

    validate_iso_string(iso_datestring)

    if (isoparse(iso_datestring).date() > datetime.today().date()):
        raise ValidationError("Dates in the future cannot be requested")
