"""
Scoot feature extraction
"""
import time
from geoalchemy2.comparator import Comparator
import pandas as pd
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from .features import Features
from ..databases import DBWriter
from ..databases.tables import MetaPoint, ScootDetector, OSHighway, ScootRoadMatch
from ..loggers import duration, get_logger, green
from ..mixins import DateRangeMixin, DBQueryMixin

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

        # # Set baseclass property 'dynamic' True to take time into account
        # self.dynamic = True

    # def match_to_roads(self):
    #     print("matching to roads")

    # @property
    # def table(self):
    #     """Join the geometry column from OSHighway onto the ScootRoadReading table for feature extraction"""
    #     with self.dbcnxn.open_session() as session:

    #         return (
    #             session.query(ScootRoadReading, OSHighway.geom)
    #             .join(OSHighway)
    #             .filter(
    #                 ScootRoadReading.measurement_start_utc >= self.start_datetime,
    #                 ScootRoadReading.measurement_start_utc < self.end_datetime,
    #             )
    #             .subquery()
    #         )

#     @property
#     def features(self):
#         return {
#             "total_occupancy_percentage": {
#                 "type": "value",
#                 "feature_dict": {"occupancy_percentage": ["*"]},
#                 "aggfunc": sum_,
#             },
#             "max_occupancy_percentage": {
#                 "type": "value",
#                 "feature_dict": {"occupancy_percentage": ["*"]},
#                 "aggfunc": max_,
#             },
#             "avg_occupancy_percentage": {
#                 "type": "value",
#                 "feature_dict": {"occupancy_percentage": ["*"]},
#                 "aggfunc": avg_,
#             },
#             "total_flow_count": {
#                 "type": "value",
#                 "feature_dict": {"flow_raw_count": ["*"]},
#                 "aggfunc": sum_,
#             },
#             "max_flow_count": {
#                 "type": "value",
#                 "feature_dict": {"flow_raw_count": ["*"]},
#                 "aggfunc": max_,
#             },
#             "avg_flow_count": {
#                 "type": "value",
#                 "feature_dict": {"flow_raw_count": ["*"]},
#                 "aggfunc": avg_,
#             },
#             "total_occupancy_count": {
#                 "type": "value",
#                 "feature_dict": {"occupancy_raw_count": ["*"]},
#                 "aggfunc": sum_,
#             },
#             "max_occupancy_count": {
#                 "type": "value",
#                 "feature_dict": {"occupancy_raw_count": ["*"]},
#                 "aggfunc": max_,
#             },
#             "avg_occupancy_count": {
#                 "type": "value",
#                 "feature_dict": {"occupancy_raw_count": ["*"]},
#                 "aggfunc": avg_,
#             },
#         }


class ScootMapToRoads(DBWriter, DBQueryMixin):
    """Map all road segments to their closest SCOOT detectors"""

    def __init__(self, **kwargs):

        # Initialise parent classes
        super().__init__(**kwargs)

        # # Subset of columns of interest for table columns
        # self.scoot_columns = [
        #     ScootDetector.toid.label("scoot_toid"),
        #     ScootDetector.detector_n.label("scoot_detector_n"),
        #     # ScootDetector.point_id.label("scoot_point_id"),
        # ]
        # self.os_highway_columns = [
        #     OSHighway.toid.label("road_toid"),
        #     OSHighway.geom.label("road_geom"),
        # ]

    def match_to_roads(self):
        """Match all road segments (OSHighway) with a SCOOT sensor (ScootDetector)"""
        start_time = time.time()

        with self.dbcnxn.open_session() as session:
            # Start by matching all detectors to the road they are on
            # NB. a single road might have multiple detectors
            #     12421 detectors only have 8160 distinct roads
            sq_roads_with_sensors = session.query(
                OSHighway.toid.label("road_toid"),
                ScootDetector.detector_n.label("scoot_detector_n"),
                func.ST_Distance(
                    func.Geography(func.ST_Centroid(OSHighway.geom)),
                    func.Geography(MetaPoint.location),
                ).label("distance_m"),
            # ).join(ScootDetector, OSHighway.toid == ScootDetector.toid).join(MetaPoint).subquery()
            ).join(ScootDetector, OSHighway.toid == ScootDetector.toid).join(MetaPoint).limit(10).subquery()

            # Load all roads that do not have sensors on them
            sq_unmatched_roads = session.query(
                OSHighway.toid.label("road_toid"),
                OSHighway.geom.label("road_geom"),
            # ).outerjoin(ScootDetector, OSHighway.toid == ScootDetector.toid).filter(ScootDetector.toid == None).subquery()
            ).outerjoin(ScootDetector, OSHighway.toid == ScootDetector.toid).filter(ScootDetector.toid == None).limit(10).subquery()

            # Get positions of all SCOOT sensors
            sq_scoot_sensors = session.query(
                MetaPoint.location,
                ScootDetector.toid.label("scoot_toid"),
                ScootDetector.detector_n.label("scoot_detector_n"),
            ).join(ScootDetector).filter(MetaPoint.source == "scoot").subquery()

            # Define a lateral query that can get the five closest sensors for a given road segment
            lateral_top5_by_distance = session.query(
                sq_unmatched_roads.c.road_toid.label("lateral_road_toid"),
                sq_scoot_sensors.c.scoot_detector_n.label("lateral_scoot_detector_n"),
                func.ST_Distance(
                    func.Geography(func.ST_Centroid(sq_unmatched_roads.c.road_geom)),
                    func.Geography(sq_scoot_sensors.c.location),
                ).label("distance_m"),
            ).order_by(
                # distance_centroid uses the PostGIS <-> operator which performs an index-based nearest neighbour search
                Comparator.distance_centroid(sq_unmatched_roads.c.road_geom, sq_scoot_sensors.c.location)
            ).limit(5).subquery().lateral()

            # fFr roads that do not have sensors on them, construct one row for each of of the five closest sensors
            q_roads_without_sensors = session.query(
                sq_unmatched_roads.c.road_toid,
                lateral_top5_by_distance.c.lateral_scoot_detector_n.label("scoot_detector_n"),
                lateral_top5_by_distance.c.distance_m
            )

            q_roads_with_sensors = session.query(sq_roads_with_sensors)
            df_matches = pd.read_sql(q_roads_with_sensors.statement, q_roads_with_sensors.session.bind)
            print("q_roads_with_sensors")
            print(df_matches.head())

            df_matches = pd.read_sql(q_roads_without_sensors.statement, q_roads_without_sensors.session.bind)
            print("q_roads_without_sensors")
            print(df_matches.head())

            # Combine the two road lists and read them into a local dataframe
            q_combined = session.query(sq_roads_with_sensors).union_all(q_roads_without_sensors)
            df_matches = pd.read_sql(q_combined.statement, q_combined.session.bind).rename(
                columns={
                    "anon_1_scoot_detector_n": "detector_n",
                    "anon_1_road_toid": "road_toid",
                    "anon_1_distance_m": "distance_m"
                }
            )
            self.logger.info("Loaded %s road-sensor associations from the database", green(df_matches.shape[0]))

            # Construct the weight column. The weight for each sensor is d / sum_0^n (d)
            df_matches["weight"] = df_matches["distance_m"].groupby(df_matches["road_toid"]).transform(lambda x: 1.0 / sum(x))
            df_matches["weight"] = df_matches["distance_m"] * df_matches["weight"]

        self.logger.info("Constructing road matches took %s", duration(start_time, time.time()))
        return df_matches


    def update_remote_tables(self):
        """Update the database with SCOOT road matches."""
        self.logger.info("Uploading %s road matches...", green("SCOOT"))
        n_records = 0

        # Get the forecasts and convert to a list of dictionaries
        road_match_records = self.match_to_roads().to_dict("records")

        # Insert road matches into the database
        if len(road_match_records) > 0:
            self.logger.info(
                "Preparing to insert %s road matches into database",
                green(len(road_match_records)),
            )

            # Open a session and insert the road matches
            start_session = time.time()
            with self.dbcnxn.open_session() as session:
                try:
                    # Commit and override any existing records
                    self.commit_records(
                        session,
                        road_match_records,
                        on_conflict="overwrite",
                        table=ScootRoadMatch,
                    )
                    n_records += len(road_match_records)
                except IntegrityError as error:
                    self.logger.error(
                        "Failed to add road matches to the database: %s", type(error)
                    )
                    self.logger.error(str(error))
                    session.rollback()

            self.logger.info("Insertion took %s", duration(start_session, time.time()))






#             scoot_distance_sq = (
#                 session.query(
#                     scoot_sensors,
#                     unmatached_roads_sq.c.geom.distance_centroid(
#                         scoot_sensors.c.location
#                     ).label("scoot_road_distance_1"),
#                     func.ST_Distance(
#                         func.ST_Centroid(unmatached_roads_sq.c.geom),
#                         scoot_sensors.c.location,
#                     ).label("scoot_road_distance"),
#                 )
#                 .order_by(
#                     asc(
#                         unmatached_roads_sq.c.geom.distance_centroid(
#                             scoot_sensors.c.location
#                         )
#                     )
#                 )
#                 .limit(5)
#                 .subquery()
#                 .lateral()
#             )


            # q_unmatched5 = session.query(sq_unmatched_roads).limit(5).all()
            # print("sq_unmatched_roads top 5:", q_unmatched5)



            # q_matched5 = session.query(sq_roads_with_sensors).limit(5).all()
            # print("sq_roads_with_sensors top 5:", q_matched5)


            # sq_roads_with_sensors = session.query(
            #         *self.scoot_columns,
            #         *self.os_highway_columns,
            #     ).join(OSHighway, ScootDetector.toid == OSHighway.identifier).filter(OSHighway.identifier == None).subquery()


            # print(q.keys())

            # identifiers = session.query(matached_roads_sq.c.road_toid).distinct()





            # q_test = session.query(
            #     sq_roads_with_sensors,
            #     sq_unmatched_roads
            # ).join()
            # print("q_test:", q_test.count())



#             unmatached_roads_sq = (
#                 session.query(*self.os_highway_columns, OSHighway.geom)
#                 .filter(
#                     OSHighway.geom.ST_Within(boundary_geom),
#                     OSHighway.identifier.notin_(identifiers),
#                 )
#                 .subquery()
#             )

#             scoot_sensors = (
#                 session.query(MetaPoint, *self.scoot_columns)
#                 .join(ScootDetector)
#                 .filter(MetaPoint.source == "scoot")
#                 .subquery()
#             )

#             scoot_distance_sq = (
#                 session.query(
#                     scoot_sensors,
#                     unmatached_roads_sq.c.geom.distance_centroid(
#                         scoot_sensors.c.location
#                     ).label("scoot_road_distance_1"),
#                     func.ST_Distance(
#                         func.ST_Centroid(unmatached_roads_sq.c.geom),
#                         scoot_sensors.c.location,
#                     ).label("scoot_road_distance"),
#                 )
#                 .order_by(
#                     asc(
#                         unmatached_roads_sq.c.geom.distance_centroid(
#                             scoot_sensors.c.location
#                         )
#                     )
#                 )
#                 .limit(5)
#                 .subquery()
#                 .lateral()
#             )





                # .except_(q_matched)


# [{
#     'name': 'scoot_toid',
#     'type': VARCHAR(),
#     'aliased': False,
#     'expr': < sqlalchemy.sql.elements.Label object at 0x7f87b00df5d0 > ,
#     'entity': < class 'cleanair.databases.tables.scoot_tables.ScootDetector' >
# }, {
#     'name': 'scoot_detector_n',
#     'type': VARCHAR(),
#     'aliased': False,
#     'expr': < sqlalchemy.sql.elements.Label object at 0x7f87a972d750 > ,
#     'entity': < class 'cleanair.databases.tables.scoot_tables.ScootDetector' >
# }, {
#     'name': 'scoot_point_id',
#     'type': UUID(),
#     'aliased': False,
#     'expr': < sqlalchemy.sql.elements.Label object at 0x7f87a964ae10 > ,
#     'entity': < class 'cleanair.databases.tables.scoot_tables.ScootDetector' >
# }, {
#     'name': 'road_identifier',
#     'type': VARCHAR(),
#     'aliased': False,
#     'expr': < sqlalchemy.sql.elements.Label object at 0x7f87a964ab10 > ,
#     'entity': < class 'cleanair.databases.tables.oshighway_table.OSHighway' >
# }, {
#     'name': 'road_toid',
#     'type': VARCHAR(),
#     'aliased': False,
#     'expr': < sqlalchemy.sql.elements.Label object at 0x7f87a9658d10 > ,
#     'entity': < class 'cleanair.databases.tables.oshighway_table.OSHighway' >
# }]


            # q2 = session.query(
            #         *self.scoot_columns,
            #         *self.os_highway_columns,
            #     ).except_(q_matched)

            #     # filter(~ exists().where(OSHighway.identifier == q.all().road_identifier))


            #         # .filter()
            # print(q2.count())


            # scoot_info_sq = (
            #     session.query(
            #         ScootDetector.toid.label("scoot_toid"),
            #         ScootDetector.detector_n.label("scoot_detector_n"),
            #         *self.os_highway_columns,
            #         func.ST_Distance(
            #             func.ST_Centroid(OSHighway.geom), MetaPoint.location
            #         ).label("scoot_road_distance")
            #     )
            #     .join(ScootDetector)
            #     .filter(
            #         MetaPoint.source == "scoot",
            #         OSHighway.identifier == ScootDetector.toid,
            #     )
            #     .subquery()
            # )


#         with self.dbcnxn.open_session() as session:



#     @db_query
#     def join_scoot_with_road(self):
#         """Match all scoot sensors (ScootDetector) with a road (OSHighway)"""

#         with self.dbcnxn.open_session() as session:

#             # Distances calculated in lat/lon
#             scoot_info_sq = (
#                 session.query(
#                     MetaPoint.id,
#                     *self.scoot_columns,
#                     *self.os_highway_columns,
#                     func.ST_Distance(
#                         func.ST_Centroid(OSHighway.geom), MetaPoint.location
#                     ).label("scoot_road_distance")
#                 )
#                 .join(ScootDetector)
#                 .filter(
#                     MetaPoint.source == "scoot",
#                     OSHighway.identifier == ScootDetector.toid,
#                 )
#                 .subquery()
#             )

#             scoot_info_q = session.query(
#                 scoot_info_sq.c.road_toid,
#                 scoot_info_sq.c.scoot_detector_n,
#                 scoot_info_sq.c.scoot_road_distance,
#             )

#             return scoot_info_q

#     @db_query
#     def join_unmatached_scoot_with_road(self):
#         """For all roads (OSHighway) not matched to a scoot sensor (ScootDetector),
#            match with the closest 5 scoot sensors"""

#         boundary_geom = self.query_london_boundary()
#         matached_roads_sq = self.join_scoot_with_road().subquery()

#         with self.dbcnxn.open_session() as session:

#             identifiers = session.query(matached_roads_sq.c.road_toid).distinct()

#             unmatached_roads_sq = (
#                 session.query(*self.os_highway_columns, OSHighway.geom)
#                 .filter(
#                     OSHighway.geom.ST_Within(boundary_geom),
#                     OSHighway.identifier.notin_(identifiers),
#                 )
#                 .subquery()
#             )

#             scoot_sensors = (
#                 session.query(MetaPoint, *self.scoot_columns)
#                 .join(ScootDetector)
#                 .filter(MetaPoint.source == "scoot")
#                 .subquery()
#             )

#             scoot_distance_sq = (
#                 session.query(
#                     scoot_sensors,
#                     unmatached_roads_sq.c.geom.distance_centroid(
#                         scoot_sensors.c.location
#                     ).label("scoot_road_distance_1"),
#                     func.ST_Distance(
#                         func.ST_Centroid(unmatached_roads_sq.c.geom),
#                         scoot_sensors.c.location,
#                     ).label("scoot_road_distance"),
#                 )
#                 .order_by(
#                     asc(
#                         unmatached_roads_sq.c.geom.distance_centroid(
#                             scoot_sensors.c.location
#                         )
#                     )
#                 )
#                 .limit(5)
#                 .subquery()
#                 .lateral()
#             )

#             cross_sq = session.query(unmatached_roads_sq, scoot_distance_sq).subquery()

#             cross_q = session.query(
#                 cross_sq.c.road_toid,
#                 cross_sq.c.scoot_detector_n,
#                 cross_sq.c.scoot_road_distance,
#             )

#         return cross_q

#     @db_query
#     def get_all_road_matched(self):
#         """Return union between ScootRoadMatch and ScootRoadUnmatched"""

#         with self.dbcnxn.open_session() as session:
#             road_matched_q = session.query(ScootRoadMatch)
#             road_unmatched_q = session.query(ScootRoadUnmatched)
#             all_road_matched_sq = road_matched_q.union_all(road_unmatched_q).subquery()

#             all_road_matched_q = session.query(
#                 all_road_matched_sq.c.dynamic_features_scoot_road_match_road_toid.label(
#                     "road_toid"
#                 ),
#                 all_road_matched_sq.c.dynamic_features_scoot_road_match_detector_n.label(
#                     "detector_n"
#                 ),
#                 all_road_matched_sq.c.dynamic_features_scoot_road_match_scoot_road_distance.label(
#                     "scoot_road_distance"
#                 ),
#             )
#         return all_road_matched_q

#     @db_query
#     def total_inverse_distance(self):
#         """Calculate the total inverse distance from each road section to the matched scoot sensors
#             Ensure ScootFeatures.insert_closest_road() has been run first
#         """

#         all_road_matched_sq = self.get_all_road_matched().subquery()

#         with self.dbcnxn.open_session() as session:

#             total_inv_dist_q = session.query(
#                 all_road_matched_sq.c.road_toid,
#                 func.sum(1 / all_road_matched_sq.c.scoot_road_distance).label(
#                     "total_inverse_distance"
#                 ),
#             ).group_by(all_road_matched_sq.c.road_toid)

#         return total_inv_dist_q

#     @db_query
#     def get_scoot_reading(self, start_date, end_date):
#         """Get the available scoot readings between start_date (inclusive) and end_date"""

#         with self.dbcnxn.open_session() as session:

#             scoot_readings_q = session.query(ScootReading).filter(
#                 ScootReading.measurement_start_utc.between(start_date, end_date)
#             )
#             return scoot_readings_q

#     @db_query
#     def weighted_average_traffic(self, start_date, end_date):
#         """
#         Get a weighted average of traffic flow metrics for each road segment
#         """

#         sr_sq = self.get_scoot_reading(start_date, end_date, output_type="subquery")
#         arm_sq = self.get_all_road_matched().subquery()

#         with self.dbcnxn.open_session() as session:
#             tid_sq = session.query(ScootRoadInverseDistance).subquery()

#         def agg_func(input_var):
#             return func.sum(
#                 input_var
#                 / (arm_sq.c.scoot_road_distance * tid_sq.c.total_inverse_distance)
#             )

#         aggregated_funcs = [
#             agg_func(sr_sq.c.occupancy_percentage).label(
#                 "occupancy_percentage_waverage"
#             ),
#             agg_func(sr_sq.c.congestion_percentage).label(
#                 "congestion_percentage_waverage"
#             ),
#             agg_func(sr_sq.c.saturation_percentage).label(
#                 "saturation_percentage_waverage"
#             ),
#             agg_func(sr_sq.c.flow_raw_count).label("flow_count_waverage"),
#             agg_func(sr_sq.c.occupancy_raw_count).label("occupancy_count_waverage"),
#             agg_func(sr_sq.c.congestion_raw_count).label("congestion_count_waverage"),
#             agg_func(sr_sq.c.saturation_raw_count).label("saturation_count_waverage"),
#         ]

#         with self.dbcnxn.open_session() as session:

#             scoot_road_distance_q = (
#                 session.query(
#                     OSHighway.toid, sr_sq.c.measurement_start_utc, *aggregated_funcs
#                 )
#                 .join(arm_sq)
#                 .join(tid_sq)
#                 .filter(sr_sq.c.detector_id == arm_sq.c.detector_n)
#             )

#             scoot_road_distance_q = scoot_road_distance_q.group_by(
#                 OSHighway.toid, sr_sq.c.measurement_start_utc
#             ).order_by(sr_sq.c.measurement_start_utc, OSHighway.toid)

#             return scoot_road_distance_q

#     def insert_closest_roads(self):
#         """Insert tables related to weighted scoot calculation.
#            Calculate the clostest scoot sensor to each road section and insert into database.
#            Insert the total inverse distance for each road segment.
#            Only needs to be recalculated if new scoot sensors have come online"""

#         # Get sensors on road segements and insert into database
#         scoot_road_matched = self.join_scoot_with_road(output_type="subquery")
#         with self.dbcnxn.open_session() as session:
#             self.logger.info("Matching all scoot sensors to road")
#             self.commit_records(
#                 session,
#                 scoot_road_matched,
#                 on_conflict="overwrite",
#                 table=ScootRoadMatch,
#             )

#         # Get unmatched road segments, find the 5 closest scoot sensors and insert into database
#         scoot_road_unmatched = self.join_unmatached_scoot_with_road(
#             output_type="subquery"
#         )
#         with self.dbcnxn.open_session() as session:
#             self.logger.info("Matching all unmatched scoot sensors to 5 closest roads")
#             self.commit_records(
#                 session,
#                 scoot_road_unmatched,
#                 on_conflict="overwrite",
#                 table=ScootRoadUnmatched,
#             )

#     def update_scoot_road_reading(self, find_closest_roads=False):
#         """Update all remote tables"""
#         if find_closest_roads:
#             self.insert_closest_roads()
#         self.update_average_traffic()
#         # total_inverse_distance = self.total_inverse_distance(output_type="subquery")
#         # with self.dbcnxn.open_session() as session:
#         #     self.logger.info("Calculating total inverse distance for each road")
#         #     self.commit_records(session, total_inverse_distance, on_conflict="overwrite", table=ScootRoadInverseDistance)

#     def update_average_traffic(self):
#         """Map scoot data to road segments and commit to database"""
#         self.logger.info(
#             "Mapping scoot readings to road segments between %s and %s",
#             self.start_datetime,
#             self.end_datetime,
#         )
#         for start_datetime in rrule.rrule(
#             rrule.HOURLY, dtstart=self.start_datetime, until=self.end_datetime
#         ):
#             end_datetime = start_datetime + datetime.timedelta(hours=1)

#             self.logger.info(
#                 "Processing data between %s and %s",
#                 green(start_datetime),
#                 green(end_datetime),
#             )

#             weighted_traffic_sq = self.weighted_average_traffic(
#                 start_datetime, end_datetime, output_type="subquery"
#             )

#             with self.dbcnxn.open_session() as session:
#                 self.commit_records(
#                     session,
#                     weighted_traffic_sq,
#                     on_conflict="ignore",
#                     table=ScootRoadReading,
#                 )
#             # return

#     # def delete_remote_entries(self):
#     #     """Remove entries from the ScootRoadReading table"""
#     #     self.logger.info(
#     #         "Deleting all scoot road match data between %s and %s",
#     #         green(self.start_datetime),
#     #         green(self.end_datetime),
#     #     )

#     #     with self.dbcnxn.open_session() as session:
#     #         drop_q = session.query(ScootRoadReading).filter(ScootRoadReading.measurement_start_utc >= self.start_datetime,
#     #                                                         ScootRoadReading.measurement_start_utc < self.end_datetime).delete()

#     @db_query
#     def get_last_scoot_road_reading(self):

#         with self.dbcnxn.open_session() as session:

#             scoot_road_reading_sq = session.query(
#                 func.max(ScootRoadReading.measurement_start_utc).label("last_processed")
#             )

#             return scoot_road_reading_sq

#     def update_remote_tables(self):

#         last_scoot_road_match = self.get_last_scoot_road_reading(output_type="list")[0]

#         if last_scoot_road_match:
#             self.logger.info(
#                 "Matching scoot data to roads from last date found in scoot_road_match. Processing from %s to %s",
#                 last_scoot_road_match,
#                 self.end_datetime,
#             )

#             weighted_traffic_sq = self.weighted_average_traffic(
#                 last_scoot_road_match, self.end_datetime, output_type="subquery"
#             )

#         else:
#             self.logger.info(
#                 "No data in scoot_road_match. Processing any available scoot data from %s to %s",
#                 "2019-01-01",
#                 self.end_datetime,
#             )

#             weighted_traffic_sq = self.weighted_average_traffic(
#                 "2019-01-01", self.end_datetime, output_type="subquery"
#             )

#         with self.dbcnxn.open_session() as session:
#             self.commit_records(
#                 session,
#                 weighted_traffic_sq,
#                 on_conflict="overwrite",
#                 table=ScootRoadReading,
#             )
