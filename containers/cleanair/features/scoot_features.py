"""
Scoot feature extraction
"""
# import time
# from geoalchemy2.comparator import Comparator
# import pandas as pd
# from sqlalchemy import func
# from sqlalchemy.exc import IntegrityError
from .features import Features
# from ..databases import DBWriter
# from ..databases.tables import MetaPoint, ScootDetector, OSHighway, ScootRoadMatch
# from ..loggers import duration, get_logger, green
from ..mixins import DateRangeMixin #, DBQueryMixin

# import datetime
# from dateutil import rrule
# from sqlalchemy import asc, func
# from sqlalchemy.sql import exists
# from .feature_funcs import sum_, avg_, max_
# from ..decorators import db_query
# from ..loggers import green
#     MetaPoint,
#     OSHighway,
#     ScootDetector,
#     ScootReading,
#     ScootRoadInverseDistance,
#     ScootRoadMatch,
#     ScootRoadReading,
#     ScootRoadUnmatched,
# )

class ScootFeatures(DateRangeMixin, Features):
    """Process scoot features"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(dynamic=True, **kwargs)

    @property
    def table(self):
        """Join the geometry column from OSHighway onto the ScootRoadReading table for feature extraction"""
        with self.dbcnxn.open_session() as session:

            return (
                session.query(ScootRoadReading, OSHighway.geom)
                .join(OSHighway)
                .filter(
                    ScootRoadReading.measurement_start_utc >= self.start_datetime,
                    ScootRoadReading.measurement_start_utc < self.end_datetime,
                )
                .subquery()
            )

    @property
    def features(self):
        return {
            "total_occupancy_percentage": {
                "type": "value",
                "feature_dict": {"occupancy_percentage": ["*"]},
                "aggfunc": sum_,
            },
            "max_occupancy_percentage": {
                "type": "value",
                "feature_dict": {"occupancy_percentage": ["*"]},
                "aggfunc": max_,
            },
            "avg_occupancy_percentage": {
                "type": "value",
                "feature_dict": {"occupancy_percentage": ["*"]},
                "aggfunc": avg_,
            },
            "total_flow_count": {
                "type": "value",
                "feature_dict": {"flow_raw_count": ["*"]},
                "aggfunc": sum_,
            },
            "max_flow_count": {
                "type": "value",
                "feature_dict": {"flow_raw_count": ["*"]},
                "aggfunc": max_,
            },
            "avg_flow_count": {
                "type": "value",
                "feature_dict": {"flow_raw_count": ["*"]},
                "aggfunc": avg_,
            },
            "total_occupancy_count": {
                "type": "value",
                "feature_dict": {"occupancy_raw_count": ["*"]},
                "aggfunc": sum_,
            },
            "max_occupancy_count": {
                "type": "value",
                "feature_dict": {"occupancy_raw_count": ["*"]},
                "aggfunc": max_,
            },
            "avg_occupancy_count": {
                "type": "value",
                "feature_dict": {"occupancy_raw_count": ["*"]},
                "aggfunc": avg_,
            },
        }