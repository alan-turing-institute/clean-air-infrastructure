"""
Mixin for checking what satellite data is in database and what is missing
"""
from datetime import timedelta
from sqlalchemy import func, text, column, String
from dateutil.parser import isoparse

from ...decorators import db_query
from ...databases.tables import (
    MetaPoint,
    StaticFeature,
)
from ...loggers import get_logger
from ...databases.base import Values


ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")


class StaticFeatureAvailabilityMixin:
    """Common database queries. Child classes must also inherit from DBWriter"""

    def __init__(self, **kwargs):
        # Pass unused arguments onwards
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)



    @db_query
    def get_static_feature_availability(
        self, feature_name, sources, exclude_has_data
    ):
        """
        Return all the intest points of a particular source which have
        been processed for a particular feature

        Args:
            feature name (str): The name of a feature
            sources (list[str]): Name of the source
            exclude_has_data (bool): Only show interest points which are missing
        """
        with self.dbcnxn.open_session() as session:

            # Create a CTE of counts of data between reference_start_date and reference_end_date
            in_data = session.query(
                StaticFeature
            ).filter(StaticFeature.feature_name == feature_name)

            in_data_cte = in_data.cte("in_data")

            available_data_q = (
                session.query(
                    MetaPoint.id,
                    in_data_cte.c.point_id.isnot(None).label("has_data")
                )
                .join(
                    in_data_cte,
                    in_data_cte.c.point_id == MetaPoint.id,
                    isouter=True,
                ).filter(MetaPoint.source.in_(sources))
            )

            if exclude_has_data:

                available_data_q = available_data_q.filter(in_data_cte.c.point_id.is_(None))

            return available_data_q
