"""
Scoot feature extraction
"""
import datetime
from dateutil import rrule
from sqlalchemy import asc, func
import datetime
from .features import Features
from .feature_funcs import sum_, avg_, max_
from ..databases import DBWriter
from ..mixins import DateRangeMixin, DBQueryMixin
from ..decorators import db_query
from ..loggers import green
from ..databases.tables import (
    OSHighway,
    ScootDetector,
    ScootReading,
    MetaPoint,
    ScootRoadMatch,
    ScootRoadUnmatched,
    ScootRoadReading,
    ScootRoadInverseDistance,
)


class ScootFeatures(Features):
    """Process scoot features"""

    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Set baseclass property 'dynamic' True to take time into account
        self.dynamic = True

    @property
    def table(self):
        """Join the geometry column from OSHighway onto the ScootRoadReading table for feature extraction"""
        with self.dbcnxn.open_session() as session:

            return (
                session.query(ScootRoadReading, OSHighway.geom)
                .join(OSHighway)
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


class ScootMapToRoads(DateRangeMixin, DBWriter, DBQueryMixin):
    """Extract features for Scoot"""

    def __init__(self, **kwargs):

        # Initialise parent classes
        super().__init__(**kwargs)

        # Subset of columns of interest for table columns
        self.scoot_columns = [
            ScootDetector.toid.label("scoot_toid"),
            ScootDetector.detector_n.label("scoot_detector_n"),
            ScootDetector.point_id.label("scoot_point_id"),
        ]
        self.os_highway_columns = [
            OSHighway.identifier.label("road_identifier"),
            OSHighway.toid.label("road_toid"),
        ]

    @db_query
    def join_scoot_with_road(self):
        """Match all scoot sensors (ScootDetector) with a road (OSHighway)"""

        with self.dbcnxn.open_session() as session:

            # Distances calculated in lat/lon
            scoot_info_sq = (
                session.query(
                    MetaPoint.id,
                    *self.scoot_columns,
                    *self.os_highway_columns,
                    func.ST_Distance(
                        func.ST_Centroid(OSHighway.geom), MetaPoint.location
                    ).label("scoot_road_distance")
                )
                .join(ScootDetector)
                .filter(
                    MetaPoint.source == "scoot",
                    OSHighway.identifier == ScootDetector.toid,
                )
                .subquery()
            )

            scoot_info_q = session.query(
                scoot_info_sq.c.road_toid,
                scoot_info_sq.c.scoot_detector_n,
                scoot_info_sq.c.scoot_road_distance,
            )

            return scoot_info_q

    @db_query
    def join_unmatached_scoot_with_road(self):
        """For all roads (OSHighway) not matched to a scoot sensor (ScootDetector),
           match with the closest 5 scoot sensors"""

        boundary_geom = self.query_london_boundary()
        matached_roads_sq = self.join_scoot_with_road().subquery()

        with self.dbcnxn.open_session() as session:

            identifiers = session.query(matached_roads_sq.c.road_toid).distinct()

            unmatached_roads_sq = (
                session.query(*self.os_highway_columns, OSHighway.geom)
                .filter(
                    OSHighway.geom.ST_Within(boundary_geom),
                    OSHighway.identifier.notin_(identifiers),
                )
                .subquery()
            )

            scoot_sensors = (
                session.query(MetaPoint, *self.scoot_columns)
                .join(ScootDetector)
                .filter(MetaPoint.source == "scoot")
                .subquery()
            )

            scoot_distance_sq = (
                session.query(
                    scoot_sensors,
                    unmatached_roads_sq.c.geom.distance_centroid(
                        scoot_sensors.c.location
                    ).label("scoot_road_distance_1"),
                    func.ST_Distance(
                        func.ST_Centroid(unmatached_roads_sq.c.geom),
                        scoot_sensors.c.location,
                    ).label("scoot_road_distance"),
                )
                .order_by(
                    asc(
                        unmatached_roads_sq.c.geom.distance_centroid(
                            scoot_sensors.c.location
                        )
                    )
                )
                .limit(5)
                .subquery()
                .lateral()
            )

            cross_sq = session.query(unmatached_roads_sq, scoot_distance_sq).subquery()

            cross_q = session.query(
                cross_sq.c.road_toid,
                cross_sq.c.scoot_detector_n,
                cross_sq.c.scoot_road_distance,
            )

        return cross_q

    @db_query
    def get_all_road_matched(self):
        """Return union between ScootRoadMatch and ScootRoadUnmatched"""

        with self.dbcnxn.open_session() as session:
            road_matched_q = session.query(ScootRoadMatch)
            road_unmatched_q = session.query(ScootRoadUnmatched)
            all_road_matched_sq = road_matched_q.union_all(road_unmatched_q).subquery()

            all_road_matched_q = session.query(
                all_road_matched_sq.c.dynamic_features_scoot_road_match_road_toid.label(
                    "road_toid"
                ),
                all_road_matched_sq.c.dynamic_features_scoot_road_match_detector_n.label(
                    "detector_n"
                ),
                all_road_matched_sq.c.dynamic_features_scoot_road_match_scoot_road_distance.label(
                    "scoot_road_distance"
                ),
            )
        return all_road_matched_q

    @db_query
    def total_inverse_distance(self):
        """Calculate the total inverse distance from each road section to the matched scoot sensors
            Ensure ScootFeatures.insert_closest_road() has been run first
        """

        all_road_matched_sq = self.get_all_road_matched().subquery()

        with self.dbcnxn.open_session() as session:

            total_inv_dist_q = session.query(
                all_road_matched_sq.c.road_toid,
                func.sum(1 / all_road_matched_sq.c.scoot_road_distance).label(
                    "total_inverse_distance"
                ),
            ).group_by(all_road_matched_sq.c.road_toid)

        return total_inv_dist_q

    @db_query
    def get_scoot_reading(self, start_date, end_date):
        """Get the available scoot readings between start_date (inclusive) and end_date"""

        with self.dbcnxn.open_session() as session:

            scoot_readings_q = session.query(ScootReading).filter(
                ScootReading.measurement_start_utc.between(start_date, end_date)
            )
            return scoot_readings_q

    @db_query
    def weighted_average_traffic(self, start_date, end_date):
        """
        Get a weighted average of traffic flow metrics for each road segment
        """

        scoot_reading_sq = self.get_scoot_reading(
            start_date, end_date, output_type="subquery"
        )
        arm_sq = self.get_all_road_matched().subquery()

        with self.dbcnxn.open_session() as session:
            tid_sq = session.query(ScootRoadInverseDistance).subquery()

        def agg_func(input_var):
            return func.sum(
                input_var
                / (arm_sq.c.scoot_road_distance * tid_sq.c.total_inverse_distance)
            )

        aggregated_funcs = [
            agg_func(scoot_reading_sq.c.occupancy_percentage).label(
                "occupancy_percentage_waverage"
            ),
            agg_func(scoot_reading_sq.c.congestion_percentage).label(
                "congestion_percentage_waverage"
            ),
            agg_func(scoot_reading_sq.c.saturation_percentage).label(
                "saturation_percentage_waverage"
            ),
            agg_func(scoot_reading_sq.c.flow_raw_count).label("flow_count_waverage"),
            agg_func(scoot_reading_sq.c.occupancy_raw_count).label(
                "occupancy_count_waverage"
            ),
            agg_func(scoot_reading_sq.c.congestion_raw_count).label(
                "congestion_count_waverage"
            ),
            agg_func(scoot_reading_sq.c.saturation_raw_count).label(
                "saturation_count_waverage"
            ),
        ]

        with self.dbcnxn.open_session() as session:

            scoot_road_distance_q = (
                session.query(
                    OSHighway.toid,
                    scoot_reading_sq.c.measurement_start_utc,
                    *aggregated_funcs
                )
                .join(arm_sq)
                .join(tid_sq)
                .filter(scoot_reading_sq.c.detector_id == arm_sq.c.detector_n)
            )

            scoot_road_distance_q = scoot_road_distance_q.group_by(
                OSHighway.toid, scoot_reading_sq.c.measurement_start_utc
            ).order_by(OSHighway.toid, scoot_reading_sq.c.measurement_start_utc)

            return scoot_road_distance_q

    def insert_closest_roads(self):
        """Insert tables related to weighted scoot calculation.
           Calculate the clostest scoot sensor to each road section and insert into database.
           Insert the total inverse distance for each road segment.
           Only needs to be recalculated if new scoot sensors have come online"""

        # Get sensors on road segements and insert into database
        scoot_road_matched = self.join_scoot_with_road(output_type="subquery")
        with self.dbcnxn.open_session() as session:
            self.logger.info("Matching all scoot sensors to road")
            self.commit_records(session, scoot_road_matched, table=ScootRoadMatch)

        # Get unmatched road segments, find the 5 closest scoot sensors and insert into database
        scoot_road_unmatched = self.join_unmatached_scoot_with_road(
            output_type="subquery"
        )
        with self.dbcnxn.open_session() as session:
            self.logger.info("Matching all unmatched scoot sensors to 5 closest roads")
            self.commit_records(session, scoot_road_unmatched, table=ScootRoadUnmatched)

        total_inverse_distance = self.total_inverse_distance(output_type="subquery")
        with self.dbcnxn.open_session() as session:
            self.logger.info("Calculating total inverse distance for each road")
            self.commit_records(
                session, total_inverse_distance, table=ScootRoadInverseDistance
            )

    @db_query
    def get_last_scoot_road_reading(self):
        """Get the last scoot road reading"""
        with self.dbcnxn.open_session() as session:

            scoot_road_reading_sq = session.query(
                func.max(ScootRoadReading.measurement_start_utc).label("last_processed")
            )

            return scoot_road_reading_sq

    def update_remote_tables(self):

        self.logger.info(
            "Matching scoot data to roads from last date found in scoot_road_match. Processing from %s to %s",
            self.start_datetime,
            self.end_datetime,
        )

        for start_datetime in rrule.rrule(
            rrule.DAILY, dtstart=self.start_datetime, until=self.end_datetime
        ):
            end_datetime = start_datetime + datetime.timedelta(days=1)

            self.logger.info(
                "Processing data between %s and %s", green(start_datetime), green(end_datetime)
            )

            weighted_traffic_sq = self.weighted_average_traffic(
                start_datetime, end_datetime, output_type="subquery"
            )

            with self.dbcnxn.open_session() as session:
                self.commit_records(
                    session,
                    weighted_traffic_sq,
                    table=ScootRoadReading,
                    on_conflict_do_nothing=True,
                )
