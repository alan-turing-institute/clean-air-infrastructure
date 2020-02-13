"""
Scoot feature extraction
"""
# import datetime
# from dateutil import rrule
# from sqlalchemy import asc, func
from sqlalchemy import func
# from sqlalchemy.sql import exists
from .features import Features
# from .feature_funcs import sum_, avg_, max_
from ..databases import DBWriter
from ..mixins import DateRangeMixin, DBQueryMixin
# from ..decorators import db_query
# from ..loggers import green
from geoalchemy2.comparator import Comparator
from ..databases.tables import MetaPoint, ScootDetector, OSHighway
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

        # Subset of columns of interest for table columns
        self.scoot_columns = [
            ScootDetector.toid.label("scoot_toid"),
            ScootDetector.detector_n.label("scoot_detector_n"),
            # ScootDetector.point_id.label("scoot_point_id"),
        ]
        self.os_highway_columns = [
            OSHighway.toid.label("road_toid"),
            OSHighway.geom.label("road_geom"),
        ]

    def match_to_roads(self):
        """Match all road segments (OSHighway) with a SCOOT sensor (ScootDetector)"""
        print("matching to roads")

        # Start by matching all detectors to the road they are on
        # NB. a single road might have multiple detectors
        #     12421 detectors only have 8160 distinct roads
        with self.dbcnxn.open_session() as session:

            # q_scoot = session.query(*self.scoot_columns).distinct()
            # print("SCOOT:", q_scoot.count())

            # q_roads = session.query(*self.os_highway_columns).distinct()
            # print("OSHighway:", q_roads.count())

            # Get positions of all SCOOT sensors
            # ['location', 'scoot_toid', 'scoot_detector_n']
            sq_scoot_sensors = session.query(
                MetaPoint.location,
                *self.scoot_columns
            ).join(ScootDetector).filter(MetaPoint.source == "scoot").subquery()
            print("sq_scoot_sensors:", session.query(sq_scoot_sensors).count())
            # print([c["name"] for c in session.query(sq_scoot_sensors).column_descriptions])
            # print(session.query(sq_scoot_sensors).limit(5).all())

            # # ['location', 'scoot_toid', 'scoot_detector_n', 'road_toid', 'road_geom']
            # sq_roads_with_sensors = session.query(
            #     MetaPoint.location,
            #     *self.scoot_columns,
            #     *self.os_highway_columns,
            # ).join(ScootDetector, OSHighway.toid == ScootDetector.toid).join(MetaPoint).subquery()
            # print("sq_roads_with_sensors:", session.query(sq_roads_with_sensors).count())
            # # print([c["name"] for c in session.query(sq_roads_with_sensors).column_descriptions])
            # # q_matched5 = session.query(sq_roads_with_sensors).limit(5).all()
            # # print("sq_roads_with_sensors top 5:", q_matched5)

            # ['location', 'scoot_toid', 'scoot_detector_n', 'road_toid', 'road_geom']

            # ['road_toid', 'scoot_detector_n', 'distance_m']
            sq_roads_with_sensors = session.query(
                ScootDetector.detector_n.label("scoot_detector_n"),
                OSHighway.toid.label("road_toid"),
                func.ST_Distance(
                    func.Geography(func.ST_Centroid(OSHighway.geom)),
                    func.Geography(MetaPoint.location),
                ).label("distance_m"),
            ).join(ScootDetector, OSHighway.toid == ScootDetector.toid).join(MetaPoint).subquery()
            print("sq_roads_with_sensors:", session.query(sq_roads_with_sensors).count())
            # print([c["name"] for c in session.query(sq_roads_with_sensors).column_descriptions])
            # q_matched5 = session.query(sq_roads_with_sensors).limit(5).all()
            # print("sq_roads_with_sensors top 5:", q_matched5)





            # ['road_toid', 'road_geom']
            sq_unmatched_roads = session.query(
                *self.os_highway_columns,
            ).outerjoin(ScootDetector, OSHighway.toid == ScootDetector.toid).filter(ScootDetector.toid == None).limit(10).subquery()
            print("sq_unmatched_roads:", session.query(sq_unmatched_roads).count())
            # print([c["name"] for c in session.query(sq_unmatched_roads).column_descriptions])
            # print(session.query(sq_unmatched_roads.c.road_toid).all())



            # Get five closest sensors for each unmatched road segment
            # xx ['location', 'scoot_toid', 'scoot_detector_n', 'road_toid', 'road_geom']
            # ['lateral_scoot_location', 'lateral_scoot_detector_n', 'lateral_road_centroid', 'lateral_road_toid']
            # ['lateral_road_toid', 'lateral_scoot_detector_n', 'distance_m']

            # Define a lateral query that can get the five closest sensors for a given road segment
            lateral_top5_by_distance = session.query(
                # sq_scoot_sensors.c.location.label("lateral_scoot_location"),
                sq_unmatched_roads.c.road_toid.label("lateral_road_toid"),
                sq_scoot_sensors.c.scoot_detector_n.label("lateral_scoot_detector_n"),
                # func.ST_Centroid(sq_unmatched_roads.c.road_geom).label("lateral_road_centroid"),
                # func.ST_Distance(
                #     func.ST_Centroid(sq_unmatched_roads.c.road_geom),
                #     sq_scoot_sensors.c.location,
                # ).label("distance_latlon"),
                func.ST_Distance(
                    func.Geography(func.ST_Centroid(sq_unmatched_roads.c.road_geom)),
                    func.Geography(sq_scoot_sensors.c.location),
                ).label("distance_m"),
            ).order_by(
                # distance_centroid uses the PostGIS <-> operator which performs an index-based nearest neighbour search
                Comparator.distance_centroid(sq_unmatched_roads.c.road_geom, sq_scoot_sensors.c.location)
            ).limit(5).subquery().lateral()

            print("lateral_top5_by_distance:", session.query(lateral_top5_by_distance).count())
            print([c["name"] for c in session.query(lateral_top5_by_distance).column_descriptions])


            # ['road_toid', 'scoot_detector_n', 'distance_m']
            # [('osgb4000000030154456', 'N31/082b1', 193.47713525),
            #  ('osgb4000000030154456', 'N31/082m1', 319.04120742),
            #  ('osgb4000000030154456', 'N31/082d1', 371.12312762),
            #  ('osgb4000000030154456', 'N31/082e1', 368.01218109),
            #  ('osgb4000000030154456', 'N31/082n1', 370.51084346),
            #  ('osgb4000000030150163', 'N19/078a1', 5355.51780324),
            #  ('osgb4000000030150163', 'N19/077a1', 5602.37304273),
            #  ('osgb4000000030150163', 'N19/111b1', 5660.81884143),
            #  ('osgb4000000030150163', 'N19/111i1', 5808.18362376),
            #  ('osgb4000000030150163', 'N19/111d1', 5808.18362376),
            q_roads_without_sensors = session.query(
                sq_unmatched_roads.c.road_toid,
                lateral_top5_by_distance.c.lateral_scoot_detector_n.label("scoot_detector_n"),
                lateral_top5_by_distance.c.distance_m
            )

            # q_roads_without_sensors = session.query(sq_unmatched_roads, lateral_top5_by_distance)
            print("q_roads_without_sensors:", q_roads_without_sensors.count())
            print([c["name"] for c in q_roads_without_sensors.column_descriptions])
            print(q_roads_without_sensors.all())


            # ['road_toid', 'lateral_scoot_detector_n', 'distance']
            q_combined = session.query(sq_roads_with_sensors).union_all(q_roads_without_sensors)
            print("q_combined:", q_combined.count())
            print([c["name"] for c in q_combined.column_descriptions])



            print("q_combined top 5:", q_combined.limit(5).all())

            # query = session.query(
            #     sq_unmatched_roads,
            # ).outerjoin(
            #     lateral_top5_by_distance, sq_unmatched_roads.c.road_toid = lateral_top5_by_distance.c.road_toid
            # )
            # print("cross_q:", query.count())


            # cross_sq = session.query(sq_unmatched_roads, lateral_top5_by_distance).subquery()
            # print("cross_sq:", session.query(cross_sq).count())

#             cross_q = session.query(
#                 cross_sq.c.road_toid,
#                 cross_sq.c.scoot_detector_n,
#                 cross_sq.c.scoot_road_distance,
#             )



# q = db.session.query(cities1000.c.name,
#                         cities1000.c.stateRegion,
#                         cities1000.c.country).\
#     order_by(
#     func.ST_Distance(cities1000.c.geom,
#                      func.Geometry(func.ST_GeographyFromText(
#                          'POINT({} {})'.format(lon, lat))))
#     ).limit(1).first()



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
