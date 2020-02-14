"""
Scoot feature extraction
"""
# import time
# from geoalchemy2.comparator import Comparator
# import pandas as pd
from sqlalchemy import func
# from sqlalchemy.exc import IntegrityError
from .features import Features
# from ..databases import DBWriter
from ..databases.tables import ScootForecast, ScootRoadMatch
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


# ScootForecast
#     detector_id = Column(
#         String(9),
#         ForeignKey("interest_points.scoot_detector.detector_n"),
#         primary_key=True,
#         nullable=False,
#     )
#     measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
#     measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
#     n_vehicles_in_interval = Column(Integer)
#     occupancy_percentage = Column(DOUBLE_PRECISION)
#     congestion_percentage = Column(DOUBLE_PRECISION)
#     saturation_percentage = Column(DOUBLE_PRECISION)


# class ScootRoadMatch(Base):
#     """Table of all roads and their associated SCOOT sensors"""

#     __tablename__ = "scoot_road_match"
#     __table_args__ = {"schema": "dynamic_features"}

#     road_toid = Column(
#         String(),
#         ForeignKey("static_data.oshighway_roadlink.toid"),
#         primary_key=True,
#         nullable=False,
#     )
#     detector_n = Column(
#         String(),
#         ForeignKey("interest_points.scoot_detector.detector_n"),
#         primary_key=True,
#         nullable=False,
#     )
#     distance_m = Column(DOUBLE_PRECISION, nullable=False)
#     weight = Column(DOUBLE_PRECISION, nullable=False)


# target
    # road_toid = Column(
    #     String(),
    #     ForeignKey("static_data.oshighway_roadlink.toid"),
    #     primary_key=True,
    #     nullable=False,
    # )
    # measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    # measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    # n_vehicles_in_interval = Column(Integer)
    # occupancy_percentage = Column(DOUBLE_PRECISION)
    # congestion_percentage = Column(DOUBLE_PRECISION)
    # saturation_percentage = Column(DOUBLE_PRECISION)



class ScootFeatures(DateRangeMixin, Features):
    """Process scoot features"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(dynamic=True, **kwargs)

    def test(self):
        with self.dbcnxn.open_session() as session:
            # q = session.query(
            #     ScootRoadMatch.road_toid,
            #     ScootRoadMatch.weight,
            #     ScootForecast,
            # ).join(ScootForecast) # , ScootRoadMatch.detector_n == ScootForecast.detector_id)

            # q = session.query(ScootRoadMatch) #.join(ScootForecast, ScootRoadMatch.detector_n == ScootForecast.detector_id)
            # q = session.query(ScootForecast) #.join(ScootForecast, ScootRoadMatch.detector_n == ScootForecast.detector_id)

            q = session.query(ScootRoadMatch).join(ScootForecast, ScootRoadMatch.detector_n == ScootForecast.detector_id)

            # 600
            # 17005
            # => 10203000

            # .join(ScootForecast, ScootRoadMatch.detector == ScootForecast.detector)

            print("query", q.count())

            # print("query", q.count())

            #     .join(OSHighway)
            #     .filter(
            #         ScootRoadReading.measurement_start_utc >= self.start_datetime,
            #         ScootRoadReading.measurement_start_utc < self.end_datetime,
            #     )
            #     .subquery()
            # )

    @property
    def table(self):
        """Join the geometry column from OSHighway onto the ScootRoadReading table for feature extraction"""
        return None
        # with self.dbcnxn.open_session() as session:

        #     return (
        #         session.query(

        #             ScootRoadMatch
        #             ScootForecast


        #             ScootRoadReading, OSHighway.geom
        #         )
        #         .join(OSHighway)
        #         .filter(
        #             ScootRoadReading.measurement_start_utc >= self.start_datetime,
        #             ScootRoadReading.measurement_start_utc < self.end_datetime,
        #         )
        #         .subquery()
        #     )

    @property
    def features(self):
        return {
            "max_n_vehicles": {
                "type": "value",
                "feature_dict": {"n_vehicles_in_interval": ["*"]},
                "aggfunc": func.max,
            },
            "avg_n_vehicles": {
                "type": "value",
                "feature_dict": {"n_vehicles_in_interval": ["*"]},
                "aggfunc": func.avg,
            },
            "max_occupancy_percentage": {
                "type": "value",
                "feature_dict": {"occupancy_percentage": ["*"]},
                "aggfunc": func.max,
            },
            "avg_occupancy_percentage": {
                "type": "value",
                "feature_dict": {"occupancy_percentage": ["*"]},
                "aggfunc": func.avg,
            },
            "max_congestion_percentage": {
                "type": "value",
                "feature_dict": {"congestion_percentage": ["*"]},
                "aggfunc": func.max,
            },
            "avg_congestion_percentage": {
                "type": "value",
                "feature_dict": {"congestion_percentage": ["*"]},
                "aggfunc": func.avg,
            },
            "max_saturation_percentage": {
                "type": "value",
                "feature_dict": {"saturation_percentage": ["*"]},
                "aggfunc": func.max,
            },
            "avg_saturation_percentage": {
                "type": "value",
                "feature_dict": {"saturation_percentage": ["*"]},
                "aggfunc": func.avg,
            },
        }




            # "total_occupancy_percentage": {
            #     "type": "value",
            #     "feature_dict": {"occupancy_percentage": ["*"]},
            #     "aggfunc": sum_,
            # },
            # "total_flow_count": {
            #     "type": "value",
            #     "feature_dict": {"flow_raw_count": ["*"]},
            #     "aggfunc": sum_,
            # },
            # "max_flow_count": {
            #     "type": "value",
            #     "feature_dict": {"flow_raw_count": ["*"]},
            #     "aggfunc": max_,
            # },
            # "avg_flow_count": {
            #     "type": "value",
            #     "feature_dict": {"flow_raw_count": ["*"]},
            #     "aggfunc": avg_,
            # },
            # "total_occupancy_count": {
            #     "type": "value",
            #     "feature_dict": {"occupancy_raw_count": ["*"]},
            #     "aggfunc": sum_,
            # },
            # "max_occupancy_count": {
            #     "type": "value",
            #     "feature_dict": {"occupancy_raw_count": ["*"]},
            #     "aggfunc": max_,
            # },
            # "avg_occupancy_count": {
            #     "type": "value",
            #     "feature_dict": {"occupancy_raw_count": ["*"]},
            #     "aggfunc": avg_,
            # },