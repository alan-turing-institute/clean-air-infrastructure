"""
UKMap Feature extraction
"""
import time
from sqlalchemy import func
from .londonboundary_reader import LondonBoundaryReader
from .interestpoint_reader import InterestPointReader
from .ukmap_reader import UKMapReader
from ..databases import features_tables, DBWriter
from ..loggers import duration, green


class FeatureExtractor(DBWriter):
    def __init__(self, **kwargs):
        self.sources = kwargs.pop("sources", [])

        # Initialise parent classes
        super().__init__(**kwargs)

        # Connect to datasource tables
        self.ukmap = UKMapReader(**kwargs)
        self.london_boundary = LondonBoundaryReader(**kwargs)
        self.interest_points = InterestPointReader(**kwargs)

        # Process interest points (These cannot be changed without redfining database schema)
        self.buffer_radii_metres = [1000, 500, 200, 100, 10]

    # def query_london_boundary(self, boundary_geom, include_sources=None, exclude_point_ids=None):

    # def query_sensor_locations(self, boundary_geom, include_sources=None, exclude_point_ids=None):
    #     _query = self.query_interest_points(boundary_geom, include_sources, exclude_point_ids)
    #     return _query

    def process_ukmap(self):
        """For each sensor location, for each feature, extract the UK map geometry for that feature in each of the buffer radii"""
        # Get list of sensors
        q_sensors = self.interest_points.query_locations(self.london_boundary.convex_hull, include_sources=self.sources) #, exclude_point_ids=already_in_features_table)

        # Iterate over each of the UK map features and calculate the overlap with the sensors
        for feature_name, q_ukmap in self.ukmap.iterate_features(): #self.london_boundary.convex_hull):
            start = time.time()
            self.logger.info("Now working on %s", green(feature_name))
            results = self.query_sensor_ukmap_intersections(q_sensors, q_ukmap).all()
            self.logger.info("Calculated %s records in %s", green(len(results)), green(duration(start, time.time())))

            with self.dbcnxn.open_session() as session:
                site_records = list(filter(None, [features_tables.build_entry(feature_name, result) for result in results]))
                if site_records:
                    self.add_records(session, site_records)
                    self.logger.info("Committing %s records to database table %s",
                                    green(len(site_records)),
                                    green(site_records[0].__tablename__))
                    session.commit()


    def query_sensor_ukmap_intersections(self, q_interest_points, q_ukmap):
        with self.dbcnxn.open_session() as session:
            # Outer join of queries: resulting in Npoints * Ngeometries records ()
            sq_all = session.query(q_interest_points.subquery(), q_ukmap.subquery()).subquery() # -> 105247 rows in 10s (after previous calls)

            # Group them by interest point: resulting in Npoints records
            sq_grouped = session.query(sq_all.c.point_id, func.max(sq_all.c.location).label("location"), func.ST_Union(func.ST_Force2D(sq_all.c.geom)).label("geoms")).group_by(sq_all.c.point_id).subquery() # -> 41 rows in 215s (after previous calls)

            # # Calculate each of the buffers: resulting in Npoints records
            # q_overlap = session.query(sq_grouped.c.point_id, *[ST_ForceCollection(ST_Intersection(func.Geometry(ST_Buffer(func.Geography(sq_grouped.c.location), distance)), sq_grouped.c.geoms)) for distance in self.buffer_sizes]) # -> 41 rows in 65s (after previous calls)
            # print("q_overlap:", q_overlap.subquery().c)
            # # q_overlap: ['%(140660624295824 anon)s.point_id', 'anon_1."ST_ForceCollection_1"', 'anon_1."ST_ForceCollection_1"', 'anon_1."ST_ForceCollection_1"', 'anon_1."ST_ForceCollection_1"', 'anon_1."ST_ForceCollection_1"']

            # Calculate the largest buffer: resulting in Npoints records
            sq_largest_buffer = session.query(sq_grouped.c.point_id, sq_grouped.c.location, func.ST_ForceCollection(func.ST_Intersection(func.Geometry(func.ST_Buffer(func.Geography(sq_grouped.c.location), max(self.buffer_radii_metres))), sq_grouped.c.geoms)).label("largest_buffer")).subquery() # -> 41 rows in 65s (after previous calls)

            # Calculate each of the buffers: resulting in Npoints records
            q_intersections = session.query(sq_largest_buffer.c.point_id, *[func.ST_ForceCollection(func.ST_Intersection(func.Geometry(func.ST_Buffer(func.Geography(sq_largest_buffer.c.location), distance)), sq_largest_buffer.c.largest_buffer)) for distance in self.buffer_radii_metres]) # -> 41 rows in 65s (after previous calls)

        # Return the overall query
        return q_intersections

