"""
Scoot feature extraction
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from sqlalchemy import between, cast, func, Integer, literal, or_, asc
from ..databases import DBWriter
from ..databases.tables import OSHighway, ScootDetector, MetaPoint, LondonBoundary, ScootRoadMatch

pd.set_option('display.max_columns', 500)

class ScootFeatures(DBWriter):
    """Extract features for Scoot"""
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # List of features to extract
        self.features = {}


        # Subset of columns of interest for table columns
        self.scoot_columns = [ScootDetector.toid.label("scoot_toid"),
                              ScootDetector.detector_n.label("scoot_detector_n"),
                              ScootDetector.point_id.label("scoot_point_id")]
        self.os_highway_columns = [OSHighway.identifier.label("road_identifier"),
                                   OSHighway.toid.label("road_toid")]

    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London"""
        with self.dbcnxn.open_session() as session:
            hull = session.scalar(func.ST_ConvexHull(func.ST_Collect(LondonBoundary.geom)))
        return hull

    def join_scoot_with_road(self):        

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
            
            scoot_sensors = session.query(MetaPoint, *self.scoot_columns).join(ScootDetector).filter(MetaPoint.source == 'scoot').subquery()

            scoot_distance_sq = session.query(scoot_sensors,
                                              unmatached_roads_sq.c.geom.distance_centroid(scoot_sensors.c.location).label('scoot_road_distance_1'),
                                              func.ST_Distance(func.ST_Centroid(unmatached_roads_sq.c.geom),
                                                               scoot_sensors.c.location).label('scoot_road_distance')) \
                                       .order_by(asc(unmatached_roads_sq.c.geom.distance_centroid(scoot_sensors.c.location))).limit(5) \
                                       .subquery() \
                                       .lateral()

            cross_sq = session.query(unmatached_roads_sq, 
                                    scoot_distance_sq).subquery()

            cross_q = session.query(cross_sq.c.road_toid, cross_sq.c.scoot_detector_n, cross_sq.c.scoot_road_distance)

            return cross_q

    def insert_closest_roads(self):
        """Calculate the clostest scoot sensor to each road section and insert into database"""

        # Get sensors on road segements and insert into database
        scoot_road_matched = self.join_scoot_with_road().subquery()
        with self.dbcnxn.open_session() as session:
            self.logger.info("Matching all scoot sensors to road")
            self.add_records(session, scoot_road_matched, table=ScootRoadMatch)

        # Get unmatched road segments, find the 5 closest scoot sensors and insert into database
        scoot_road_unmatched = self.join_unmatached_scoot_with_road().subquery()
        with self.dbcnxn.open_session() as session:
            self.logger.info("Matching all unmatched scoot sensors to 5 closest roads")
            self.add_records(session, scoot_road_unmatched, table=ScootRoadMatch)

    def update_remote_tables(self):
        """Update all remote tables"""
        self.insert_closest_roads()
