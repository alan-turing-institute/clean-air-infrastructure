"""
Mixin for checking what Breathe London data is in database and what is missing
"""
from typing import Optional
from datetime import timedelta
from sqlalchemy import func, text
from dateutil.parser import isoparse

from ...decorators import db_query
from ...databases.tables import MetaPoint, AQESite, AQEReading
from ...loggers import get_logger


ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")

class BreatheAvailabilityMixin:
    """Common database queries. Child classes must also inherit from DBWriter"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @db_query()
    def get_laqn_open_sites(self, exclude_closed=True):
        """Get open LAQN sites

        Some LAQN sites have more than one sitecode but have the same location.
        Considers these as one site.
        """