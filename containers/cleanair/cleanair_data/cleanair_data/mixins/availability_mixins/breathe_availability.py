"""
Mixin for checking what Breathe London data is in database and what is missing
"""
from typing import Optional
from datetime import timedelta
from sqlalchemy import func, text
from dateutil.parser import isoparse

from ...decorators import db_query
from ...databases.tables.breathe_tables import BreatheSite, BreatheReading
from ...databases.tables import MetaPoint
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
    def get_breathe_open_sites(self, exclude_closed=True):
        """Get open Breathe sites

        Some BL sites have more than one sitecode but have the same location.
        Considers these as one site.
        """

        with self.dbcnxn.open_session() as session:
            # uses the SQL functions to block doubled site code and gets the max and min time loop of the site
            columns = [
                BreatheSite.point_id,
                func.array_agg(BreatheSite.site_code).label("site_codes"),
                func.min(BreatheSite.date_opened).label("date_opened"),
                func.max(BreatheSite.date_closed).label("date_closed"),
            ]

            breathe_site_q = session.query(*columns).group_by(BreatheSite.point_id)

            breathe_site_sq = breathe_site_q.order_by(BreatheSite.point_id).subquery()

            if exclude_closed:
                return session.query(breathe_site_sq).filter(
                    breathe_site_sq.c.date_closed.is_(None)
                )

            return session.query(breathe_site_sq)

            return breathe_site_q
