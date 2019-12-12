"""
Scoot feature extraction
"""
import pandas as pd
from dateutil.parser import isoparse
from sqlalchemy import asc, func
from .static_features import Features
from ..mixins import DateRangeMixin
from ..databases.tables import (OSHighway, ScootDetector, ScootReading,
                                MetaPoint, ScootRoadMatch, ScootRoadUnmatched,
                                ScootRoadReading)


class ScootFeatures(DateRangeMixin, Features):
    """Extract features for Scoot"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # List of features to extract
        self.features = {}

        # Subset of columns of interest for table columns
        self.scoot_columns = [ScootDetector.toid.label("scoot_toid"),
                              ScootDetector.detector_n.label("scoot_detector_n"),
                              ScootDetector.point_id.label("scoot_point_id")]
        self.os_highway_columns = [OSHighway.identifier.label("road_identifier"),
                                   OSHighway.toid.label("road_toid")]

    def join_scoot_with_road(self):
        """Match all scoot sensors (ScootDetector) with a road (OSHighway)"""

        with self.dbcnxn.open_session() as session:

            # Distances calculated in lat/lon
            scoot_info_sq = session.query(MetaPoint.id,
                                          *self.scoot_columns,
                                          *self.os_highway_columns,
                                          func.ST_Distance(func.ST_Centroid(OSHighway.geom),
                                                           MetaPoint.location).label('scoot_road_distance')
                                          ) \
                .join(ScootDetector) \
                .filter(MetaPoint.source == 'scoot',
                        OSHighway.identifier == ScootDetector.toid) \
                .subquery()

            scoot_info_q = session.query(scoot_info_sq.c.road_toid,
                                         scoot_info_sq.c.scoot_detector_n,
                                         scoot_info_sq.c.scoot_road_distance)

            return scoot_info_q

    def join_unmatached_scoot_with_road(self):
        """For all roads (OSHighway) not matched to a scoot sensor (ScootDetector), 
           match with the closest 5 scoot sensors"""

        boundary_geom = self.query_london_boundary()
        matached_roads_sq = self.join_scoot_with_road().subquery()

        with self.dbcnxn.open_session() as session:

            identifiers = session.query(matached_roads_sq.c.road_toid).distinct()

            unmatached_roads_sq = session.query(*self.os_highway_columns,
                                                OSHighway.geom) \
                .filter(OSHighway.geom.ST_Within(boundary_geom),
                        OSHighway.identifier.notin_(identifiers)
                        ) \
                .subquery()

            scoot_sensors = session.query(MetaPoint,
                                          *self.scoot_columns).join(ScootDetector) \
                                                              .filter(MetaPoint.source == 'scoot') \
                                                              .subquery()

            scoot_distance_sq = session.query(scoot_sensors,
                                              unmatached_roads_sq.c.geom.distance_centroid(
                                                  scoot_sensors.c.location).label('scoot_road_distance_1'),
                                              func.ST_Distance(func.ST_Centroid(unmatached_roads_sq.c.geom),
                                                               scoot_sensors.c.location).label('scoot_road_distance')) \
                .order_by(asc(unmatached_roads_sq.c.geom.distance_centroid(scoot_sensors.c.location))).limit(5) \
                .subquery() \
                .lateral()

            cross_sq = session.query(unmatached_roads_sq,
                                     scoot_distance_sq).subquery()

            cross_q = session.query(cross_sq.c.road_toid, cross_sq.c.scoot_detector_n, cross_sq.c.scoot_road_distance)

            return cross_q

    def get_all_road_matched(self):
        """Return union between ScootRoadMatch and ScootRoadUnmatched"""

        with self.dbcnxn.open_session() as session:
            road_matched_q = session.query(ScootRoadMatch)
            road_unmatched_q = session.query(ScootRoadUnmatched)
            all_road_matched_sq = road_matched_q.union_all(road_unmatched_q).subquery()

            all_road_matched_q = session.query(
                all_road_matched_sq.c.dynamic_features_scoot_road_match_road_toid.label('road_toid'),
                all_road_matched_sq.c.dynamic_features_scoot_road_match_detector_n.label('detector_n'),
                all_road_matched_sq.c.dynamic_features_scoot_road_match_scoot_road_distance.label('scoot_road_distance')
            )
            return all_road_matched_q

    def total_inverse_distance(self):
        """Calculate the total inverse distance from each road section to the matched scoot sensors
            Ensure ScootFeatures.insert_closest_road() has been run first
        """

        all_road_matched_sq = self.get_all_road_matched().subquery()

        with self.dbcnxn.open_session() as session:

            total_inverse_distance_q = session.query(all_road_matched_sq.c.road_toid,
                                                     func.sum(
                                                         1/all_road_matched_sq.c.scoot_road_distance).label("total_inverse_distance")
                                                     ).group_by(all_road_matched_sq.c.road_toid)

            return total_inverse_distance_q

    def get_scoot_reading(self, start_date, end_date):
        """Get the available scoot readings between start_date (inclusive) and end_date"""

        with self.dbcnxn.open_session() as session:

            scoot_readings_q = session.query(ScootReading) \
                .filter(ScootReading.measurement_start_utc.between(start_date,
                                                                   end_date))
            return scoot_readings_q

    def weighted_average_traffic(self, start_date, end_date):
        """
        Get a weighted average of traffic flow metrics for each road segment
        """
    
        scoot_readings_sq = self.get_scoot_reading(start_date, end_date).subquery()
        all_road_matched_sq = self.get_all_road_matched().subquery()
        total_inverse_distance_sq = self.total_inverse_distance().subquery()

        aggregate_funcs = [func.sum(scoot_readings_sq.c.occupancy_percentage /
                                   (all_road_matched_sq.c.scoot_road_distance * total_inverse_distance_sq.c.total_inverse_distance)).label("occupancy_percentage_waverage"),
                            func.sum(scoot_readings_sq.c.congestion_percentage /
                                   (all_road_matched_sq.c.scoot_road_distance * total_inverse_distance_sq.c.total_inverse_distance)).label("congestion_percentage_waverage"),
                            func.sum(scoot_readings_sq.c.saturation_percentage /
                                   (all_road_matched_sq.c.scoot_road_distance * total_inverse_distance_sq.c.total_inverse_distance)).label("saturation_percentage_waverage"),
                            func.sum(scoot_readings_sq.c.flow_raw_count /
                                   (all_road_matched_sq.c.scoot_road_distance * total_inverse_distance_sq.c.total_inverse_distance)).label("flow_count_waverage"),
                            func.sum(scoot_readings_sq.c.occupancy_raw_count /
                                   (all_road_matched_sq.c.scoot_road_distance * total_inverse_distance_sq.c.total_inverse_distance)).label("occupancy_count_waverage"),
                            func.sum(scoot_readings_sq.c.congestion_raw_count /
                                   (all_road_matched_sq.c.scoot_road_distance * total_inverse_distance_sq.c.total_inverse_distance)).label("congestion_count_waverage"),
                            func.sum(scoot_readings_sq.c.saturation_raw_count /
                                   (all_road_matched_sq.c.scoot_road_distance * total_inverse_distance_sq.c.total_inverse_distance)).label("saturation_count_waverage"),
                          ]

        with self.dbcnxn.open_session() as session:

            scoot_road_distance_q = session.query(OSHighway.toid,
                                                  scoot_readings_sq.c.measurement_start_utc,
                                                  *aggregate_funcs) \
                                                      .join(all_road_matched_sq) \
                                                      .join(total_inverse_distance_sq) \
                                                       .filter(scoot_readings_sq.c.detector_id == all_road_matched_sq.c.detector_n)

            scoot_road_distance_q = scoot_road_distance_q.group_by(OSHighway.toid, scoot_readings_sq.c.measurement_start_utc) \
                                                         .order_by(OSHighway.toid, scoot_readings_sq.c.measurement_start_utc)

            return scoot_road_distance_q

    def insert_closest_roads(self):
        """Calculate the clostest scoot sensor to each road section and insert into database
        Only needs to be recalculated if new scoot sensors have come online"""

        # Get sensors on road segements and insert into database
        scoot_road_matched = self.join_scoot_with_road().subquery()
        with self.dbcnxn.open_session() as session:
            self.logger.info("Matching all scoot sensors to road")
            self.add_records(session, scoot_road_matched, table=ScootRoadMatch)

        # Get unmatched road segments, find the 5 closest scoot sensors and insert into database
        scoot_road_unmatched = self.join_unmatached_scoot_with_road().subquery()
        with self.dbcnxn.open_session() as session:
            self.logger.info("Matching all unmatched scoot sensors to 5 closest roads")
            self.add_records(session, scoot_road_unmatched, table=ScootRoadUnmatched)

    def update_average_traffic(self):

        self.logger.info("Mapping scoot readings to road segments between %s and %s", self.start_datetime, self.end_datetime)
        traffic_q = self.weighted_average_traffic(self.start_datetime, self.end_datetime)
        with self.dbcnxn.open_session() as session:
            self.add_records(session, traffic_q.subquery(), table=ScootRoadReading)

    def update_remote_tables(self, find_closest_roads=False):
        """Update all remote tables"""
        if find_closest_roads:
            self.insert_closest_roads()
        self.update_average_traffic()
