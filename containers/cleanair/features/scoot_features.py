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

        # List of features to extract
        self.features = {}


        self.scoot_columns = [ScootDetector.toid,
                              ScootDetector.detector_n,
                              ScootDetector.point_id]

        self.os_highway_columns = [OSHighway.identifier]

    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London"""
        with self.dbcnxn.open_session() as session:
            hull = session.scalar(func.ST_ConvexHull(func.ST_Collect(LondonBoundary.geom)))
        return hull

    def join_scoot_with_road(self):        

        with self.dbcnxn.open_session() as session:

            # Distances calculated in lat/lon
            scoot_info_q = session.query(MetaPoint.id, 
                                         *self.scoot_columns,
                                         *self.os_highway_columns, 
                                         func.ST_Distance(func.ST_Centroid(OSHighway.geom),
                                                          MetaPoint.location).label('scoot_road_distance')
                                         ) \
                                  .join(ScootDetector) \
                                  .filter(MetaPoint.source == 'scoot', 
                                          OSHighway.identifier == ScootDetector.toid)

            return scoot_info_q
           
            

    def join_unmatached_scoot_with_road(self):

        boundary_geom = self.query_london_boundary()
        matached_roads_sq = self.join_scoot_with_road().subquery()

        with self.dbcnxn.open_session() as session:

            identifiers = session.query(matached_roads_sq.c.identifier).distinct()
            unmatached_roads_q = session.query(OSHighway
                                              ) \
                                        .filter(OSHighway.geom.ST_Within(boundary_geom),
                                                OSHighway.identifier.notin_(identifiers)
                                                ) \
                                        .limit(10) \
                                        .subquery()
            
            scoots = session.query(MetaPoint, *self.scoot_columns).join(ScootDetector).filter(MetaPoint.source == 'scoot').subquery()

            scoot_distance_sq = session.query(scoots,
                                             unmatached_roads_q.c.geom.distance_centroid(scoots.c.location).label('scoot_road_distance_1'),
                                             func.ST_Distance(func.ST_Centroid(unmatached_roads_q.c.geom),
                                                          scoots.c.location).label('scoot_road_distance')) \
                                       .order_by(asc(unmatached_roads_q.c.geom.distance_centroid(scoots.c.location))).limit(5) \
                                      .subquery() \
                                      .lateral()

            cross_q = session.query(unmatached_roads_q, 
                                    scoot_distance_sq)

            # print(cross_q.statement)
            # print(session.query(unmatached_roads_q).count())
            # print(cross_q.count())

            df = gpd.GeoDataFrame.from_postgis(cross_q.statement, cross_q.session.bind, geom_col='location')
            df2 = gpd.GeoDataFrame.from_postgis(cross_q.statement, cross_q.session.bind, geom_col='geom')       
            
            fig, ax = plt.subplots(figsize = (20,16)) 

            df.plot(column='identifier', ax=ax, legend=True, alpha = 0.4)  
            df2.plot(column='identifier', ax=ax, legend=True)
            plt.savefig('/secrets/plot.png')  

    def insert_records(self, insert_stmt, indexes, table_name):
        """Query-and-insert in one statement to reduce local memory overhead and remove database round-trips"""
        start = time.time()
        self.logger.info("Constructing features to merge into database table %s...", green(table_name))
        with self.dbcnxn.open_session() as session:
            session.execute(insert_stmt.on_conflict_do_nothing(index_elements=indexes))
            session.commit()
        self.logger.info("Finished merging feature batch into database after %s", green(duration(start, time.time())))

        select_stmt = self.query_feature_values(feature_name, q_batch, q_source).subquery().select()
        columns = [c.key for c in IntersectionValue.__table__.columns]
        insert_stmt = insert(IntersectionValue).from_select(columns, select_stmt)
        indexes = [IntersectionValue.point_id, IntersectionValue.feature_name]

    def update_remote_tables(self):
        """Update all remote tables"""
        self.join_scoot_with_road()
        # self.join_unmatached_scoot_with_road()