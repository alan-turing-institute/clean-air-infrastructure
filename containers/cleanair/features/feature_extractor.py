"""
UKMap Feature extraction
"""
import time
from sqlalchemy import func, or_
from ..databases import features_tables, interest_point_table, londonboundary_table, ukmap_table, DBWriter
from ..loggers import duration, green


class FeatureExtractor(DBWriter):
    def __init__(self, **kwargs):
        self.sources = kwargs.pop("sources", [])

        # Initialise parent classes
        super().__init__(**kwargs)

        # List of features to extract
        self.ukmap_features = {
            "museums": {"landuse": ["Museum"]},
            "hospitals": {"landuse": ["Hospitals"]},
            "grass": {"feature_type": ["Vegetated"]},
            "park": {"feature_type": ["Vegetated"], "landuse": ["Recreational open space"]},
            "water": {"feature_type": "Water"},
            "flat": {"feature_type": ["Vegetated", "Water"]},
        }

        # Radius around each interest point used for feature extraction.
        # Changing these would require redefining the database schema
        self.buffer_radii_metres = [1000, 500, 200, 100, 10]

    def query_london_boundary(self):
        with self.dbcnxn.open_session() as session:
            hull = session.scalar(func.ST_ConvexHull(func.ST_Collect(londonboundary_table.LondonBoundary.geom)))
        return hull

    def query_sensor_locations(self, include_sources=None, exclude_point_ids=None):
        boundary_geom = self.query_london_boundary()
        with self.dbcnxn.open_session() as session:
            _query = session.query(interest_point_table.InterestPoint).filter(interest_point_table.InterestPoint.location.ST_Within(boundary_geom))
            if include_sources:
                _query = _query.filter(interest_point_table.InterestPoint.source.in_(include_sources))
            if exclude_point_ids:
                _query = _query.filter(interest_point_table.InterestPoint.point_id.notin_(exclude_point_ids))
        return _query

    def iterate_ukmap_features(self):
        for feature_name, feature_dict in self.ukmap_features.items():
            with self.dbcnxn.open_session() as session:
                q_ukmap = session.query(ukmap_table.UKMap.geom, ukmap_table.UKMap.landuse, ukmap_table.UKMap.feature_type)
                for column, values in feature_dict.items():
                    q_ukmap = q_ukmap.filter(or_([getattr(ukmap_table.UKMap, column) == value for value in values]))
            yield (feature_name, q_ukmap)

    def query_sensor_ukmap_intersections(self, q_interest_points, q_ukmap):
        with self.dbcnxn.open_session() as session:
            # Outer join of queries: resulting in Npoints * Ngeometries records ()
            sq_all = session.query(q_interest_points.subquery(), q_ukmap.subquery()).subquery() # -> 105247 rows in 10s (after previous calls)

            # Group them by interest point: resulting in Npoints records
            sq_grouped = session.query(sq_all.c.point_id, func.max(sq_all.c.location).label("location"), func.ST_Union(func.ST_Force2D(func.ST_MakeValid(sq_all.c.geom))).label("geoms")).group_by(sq_all.c.point_id).subquery() # -> 41 rows in 215s (after previous calls)

            # Calculate the largest buffer: resulting in Npoints records
            sq_largest_buffer = session.query(sq_grouped.c.point_id, sq_grouped.c.location, func.ST_ForceCollection(func.ST_Intersection(func.Geometry(func.ST_Buffer(func.Geography(sq_grouped.c.location), max(self.buffer_radii_metres))), sq_grouped.c.geoms)).label("largest_buffer")).subquery() # -> 41 rows in 65s (after previous calls)

            # Calculate each of the buffers: resulting in Npoints records
            q_intersections = session.query(sq_largest_buffer.c.point_id, *[func.ST_ForceCollection(func.ST_Intersection(func.Geometry(func.ST_Buffer(func.Geography(sq_largest_buffer.c.location), distance)), sq_largest_buffer.c.largest_buffer)) for distance in self.buffer_radii_metres]) # -> 41 rows in 65s (after previous calls)

        # Return the overall query
        return q_intersections

    def process_ukmap(self):
        """For each sensor location, for each feature, extract the UK map geometry for that feature in each of the buffer radii"""
        # Get list of sensors
        q_sensors = self.query_sensor_locations(include_sources=self.sources)

        # Iterate over each of the UK map features and calculate the overlap with the sensors
        for feature_name, q_ukmap in self.iterate_ukmap_features():
            # Construct one tuple for each sensor, consisting of the point_id and a geometry collection for each radius
            start = time.time()
            self.logger.info("Now working on the %s feature", green(feature_name))
            results = self.query_sensor_ukmap_intersections(q_sensors, q_ukmap).all()
            self.logger.info("Constructed %s records in %s", green(len(results)), green(duration(start, time.time())))

            # Convert the query output into database records and merge these into the existing table
            with self.dbcnxn.open_session() as session:
                site_records = list(filter(None, [features_tables.UKMapIntersections.build_entry(feature_name, result) for result in results]))
                if site_records:
                    self.add_records(session, site_records)
                    self.logger.info("Committing %s records to database table %s",
                                    green(len(site_records)),
                                    green(features_tables.UKMapIntersections.__tablename__))
                    session.commit()



