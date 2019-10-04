"""
UKMap Feature extraction
"""
import time
from sqlalchemy import func, or_, between, cast, Integer
from ..databases import DBWriter
from ..databases.tables import InterestPoint, LondonBoundary, UKMap, UKMapIntersectionGeoms, UKMapIntersectionValues
from ..loggers import duration, green


class FeatureExtractor(DBWriter):
    def __init__(self, **kwargs):
        self.sources = kwargs.pop("sources", [])

        # Initialise parent classes
        super().__init__(**kwargs)

        # List of features to extract
        self.ukmap_features = {
            "building_height": {"feature_type": ["Building"]},
            "museums": {"landuse": ["Museum"]},
            "hospitals": {"landuse": ["Hospitals"]},
            "grass": {"feature_type": ["Vegetated"]},
            "park": {"feature_type": ["Vegetated"], "landuse": ["Recreational open space"]},
            "water": {"feature_type": ["Water"]},
            "flat": {"feature_type": ["Vegetated", "Water"]},
        }

        # Radius around each interest point used for feature extraction.
        # Changing these would require redefining the database schema
        self.buffer_radii_metres = [1000, 500, 200, 100, 10]

    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London"""
        with self.dbcnxn.open_session() as session:
            hull = session.scalar(func.ST_ConvexHull(func.ST_Collect(LondonBoundary.geom)))
        return hull

    def query_sensor_locations(self, include_sources=None):
        """Query InterestPoints, selecting all matching include_sources"""
        boundary_geom = self.query_london_boundary()
        with self.dbcnxn.open_session() as session:
            _query = session.query(InterestPoint).filter(InterestPoint.location.ST_Within(boundary_geom))
            if include_sources:
                _query = _query.filter(InterestPoint.source.in_(include_sources))
        return _query

    def query_ukmap_features(self, feature_name, feature_dict):
        """Query UKMap, selecting all features matching the requirements in feature_dict"""
        with self.dbcnxn.open_session() as session:
            if feature_name == "building_height":
                q_ukmap = session.query(UKMap.geom, UKMap.calculated_height_of_building, UKMap.feature_type)
            else:
                q_ukmap = session.query(UKMap.geom, UKMap.landuse, UKMap.feature_type)
            for column, values in feature_dict.items():
                q_ukmap = q_ukmap.filter(or_(*[getattr(UKMap, column) == value for value in values]))
        return q_ukmap

    def query_feature_intersection_geoms(self, q_interest_points, q_ukmap):
        """Construct one record for each interest point containing the point ID and one geometry column per buffer"""
        with self.dbcnxn.open_session() as session:
            # Outer join of queries: [Npoints * Ngeometries records]
            sq_all = session.query(q_interest_points.subquery(), q_ukmap.subquery()).subquery()

            # Group these by interest point: [Npoints records]
            sq_grouped = session.query(sq_all.c.point_id, func.max(sq_all.c.location).label("location"), func.ST_Union(func.ST_Force2D(func.ST_MakeValid(sq_all.c.geom))).label("geoms")).group_by(sq_all.c.point_id).subquery()

            # Calculate the largest buffer: [Npoints records]
            sq_largest_buffer = session.query(sq_grouped.c.point_id, sq_grouped.c.location, func.ST_ForceCollection(func.ST_Intersection(func.Geometry(func.ST_Buffer(func.Geography(sq_grouped.c.location), max(self.buffer_radii_metres))), sq_grouped.c.geoms)).label("largest_buffer")).subquery()

            # Calculate each of the buffers: [Npoints records]
            q_intersections = session.query(sq_largest_buffer.c.point_id, *[func.ST_ForceCollection(func.ST_Intersection(func.Geometry(func.ST_Buffer(func.Geography(sq_largest_buffer.c.location), distance)), sq_largest_buffer.c.largest_buffer)) for distance in self.buffer_radii_metres])

        # Return the overall query
        return q_intersections

    def query_feature_intersection_values(self, q_interest_points, q_ukmap):
        """Construct one record for each interest point containing the point ID and one value column per buffer"""
        with self.dbcnxn.open_session() as session:
            # Outer join of queries: [Npoints * Ngeometries records]
            sq_all = session.query(q_interest_points.subquery(), q_ukmap.subquery()).subquery()

            # Calculate the distance to each geometry, filtering to restrict to only those records within maximum buffer
            # size: [M < Npoints * Ngeometries records]
            sq_distance = session.query(sq_all.c.point_id, sq_all.c.calculated_height_of_building, func.ST_Distance(func.Geography(sq_all.c.location), func.Geography(sq_all.c.geom)).label("distance")).filter(func.ST_DWithin(func.Geography(sq_all.c.location), func.Geography(sq_all.c.geom), max(self.buffer_radii_metres))).subquery()

            # Construct new column for each buffer containing the building height iff the distance is less than the
            # buffer radius: [M records]
            sq_buffers = session.query(sq_distance.c.point_id, *[(sq_distance.c.calculated_height_of_building * cast(between(sq_distance.c.distance, 0, radius), Integer)).label(str(radius)) for radius in self.buffer_radii_metres]).subquery()

            # Group these by interest point: [Npoints records]
            q_grouped = session.query(sq_buffers.c.point_id, *[func.max(getattr(sq_buffers.c, str(radius))) for radius in self.buffer_radii_metres]).group_by(sq_buffers.c.point_id)

        # Return the overall query
        return q_grouped

    def calculate_ukmap_intersections(self):
        """For each sensor location, for each feature, extract the UK map geometry for that feature in each of the buffer radii"""
        # Get all sensors of interest
        q_sensors = self.query_sensor_locations(include_sources=self.sources)

        # Iterate over each of the UK map features and calculate the overlap with the sensors
        for feature_name, feature_dict in self.ukmap_features.items():
            start = time.time()
            self.logger.info("Now working on the %s feature", green(feature_name))

            # Get UKMap geometries for this feature
            q_ukmap = self.query_ukmap_features(feature_name, feature_dict)

            # Construct one tuple for each sensor, consisting of the point_id and a geometry collection for each radius
            if feature_name == "building_height":
                results = self.query_feature_intersection_values(q_sensors, q_ukmap).all()
                site_records = list(filter(None, [UKMapIntersectionValues.build_entry(feature_name, result) for result in results]))
            else:
                results = self.query_feature_intersection_geoms(q_sensors, q_ukmap).all()
                site_records = list(filter(None, [UKMapIntersectionGeoms.build_entry(feature_name, result) for result in results]))
            self.logger.info("Constructed %s records in %s", green(len(results)), green(duration(start, time.time())))

            # Convert the query output into database records and merge these into the existing table
            with self.dbcnxn.open_session() as session:
                if site_records:
                    self.add_records(session, site_records)
                    self.logger.info("Committing %s records to database table %s",
                                     green(len(site_records)),
                                     green(site_records[0].__tablename__))
                    session.commit()

    def update_remote_tables(self):
        """Update all remote tables"""
        self.calculate_ukmap_intersections()



