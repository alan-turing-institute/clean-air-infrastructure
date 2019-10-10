"""
Feature extraction Base  class
"""
import time
from sqlalchemy import func, or_, between, cast, Integer, literal
from sqlalchemy.dialects.postgresql import insert
from ..databases import DBWriter
from ..databases.tables import InterestPoint, LondonBoundary, IntersectionGeoms, IntersectionValues
from ..loggers import duration, green


class StaticFeatures(DBWriter):
    """Extract features which are near to sensor InterestPoints and inside London"""
    def __init__(self, **kwargs):
        self.sources = kwargs.pop("sources", [])

        # Initialise parent classes
        super().__init__(**kwargs)

        # Radius around each interest point used for feature extraction.
        # Changing these would require redefining the database schema
        self.buffer_radii_metres = [1000, 500, 200, 100, 10]

    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London"""
        with self.dbcnxn.open_session() as session:
            hull = session.scalar(func.ST_ConvexHull(func.ST_Collect(LondonBoundary.geom)))
        return hull

    def query_sensor_locations(self, include_sources=None, with_buffers=False):
        """Query InterestPoints, selecting all matching include_sources"""
        boundary_geom = self.query_london_boundary()
        with self.dbcnxn.open_session() as session:
            columns = [InterestPoint, func.Geography(InterestPoint.location).label("location_geog")]
            if with_buffers:
                columns += [func.Geometry(func.ST_Buffer(func.Geography(InterestPoint.location), rad)).label(str(rad))
                            for rad in self.buffer_radii_metres]
            _query = session.query(*columns).filter(InterestPoint.location.ST_Within(boundary_geom))
            if include_sources:
                _query = _query.filter(InterestPoint.source.in_(include_sources))
        return _query


    def query_feature_geoms(self, feature_type, q_interest_points, q_geometries):
        """Construct one record for each interest point containing the point ID and one geometry column per buffer"""
        with self.dbcnxn.open_session() as session:
            # Outer join of queries: [Npoints * Ngeometries records]
            sq_all = session.query(q_interest_points.subquery(), q_geometries.subquery()).subquery()

            # Restrict to only those within max(radius) of one another: [M < Npoints * Ngeometries records]
            sq_within = session.query(sq_all).filter(func.ST_DWithin(sq_all.c.location_geog,
                                                                     sq_all.c.geom_geog,
                                                                     max(self.buffer_radii_metres))).subquery()

            # Add intersection columns containing the intersection with each buffer: [M records]
            sq_with_buffers = session.query(sq_within.c.point_id,
                                            *[func.ST_Intersection(getattr(sq_within.c, str(radius)),
                                                                   sq_within.c.geom).label("intst_{}".format(radius))
                                              for radius in self.buffer_radii_metres]
                                            ).subquery()

            # Group these by interest point, unioning geometries: [Npoints records]
            q_intersections = session.query(sq_with_buffers.c.point_id,
                                            literal(feature_type).label("feature_type"),
                                            *[func.ST_ForceCollection(
                                                func.ST_Union(getattr(sq_with_buffers.c, "intst_{}".format(radius)))
                                                ).label("geom_{}".format(radius))
                                              for radius in self.buffer_radii_metres]
                                            ).group_by(sq_with_buffers.c.point_id)

        # Return the overall query
        return q_intersections

    def query_feature_values(self, feature_type, q_interest_points, q_geometries):
        """Construct one record for each interest point containing the point ID and one value column per buffer"""
        with self.dbcnxn.open_session() as session:
            # Outer join of queries: [Npoints * Ngeometries records]
            sq_all = session.query(q_interest_points.subquery(), q_geometries.subquery()).subquery()

            # Restrict to only those within max(radius) of one another: [M < Npoints * Ngeometries records]
            sq_within = session.query(sq_all).filter(func.ST_DWithin(sq_all.c.location_geog,
                                                                     sq_all.c.geom_geog,
                                                                     max(self.buffer_radii_metres))).subquery()

            # Filter out unreasonably tall buildings: [M records]
            sq_filtered = session.query(sq_within).filter(sq_within.c.calculated_height_of_building < 999.9).subquery()

            # Calculate the distance to each geometry: [M records]
            sq_distance = session.query(sq_filtered.c.point_id,
                                        sq_filtered.c.calculated_height_of_building,
                                        func.ST_Distance(sq_filtered.c.location_geog,
                                                         sq_filtered.c.geom_geog).label("distance")
                                        ).subquery()

            # Construct new column for each buffer containing the building height iff the distance is less than the
            # buffer radius: [M records]
            sq_with_buffers = session.query(sq_distance.c.point_id,
                                            *[(sq_distance.c.calculated_height_of_building *
                                               cast(between(sq_distance.c.distance, 0, radius), Integer)
                                               ).label(str(radius)) for radius in self.buffer_radii_metres]).subquery()

            # Group these by interest point: [Npoints records]
            q_intersections = session.query(sq_with_buffers.c.point_id,
                                            literal(feature_type).label("feature_type"),
                                            *[func.max(getattr(sq_with_buffers.c,
                                                               str(radius))).label("value_{}".format(radius))
                                              for radius in self.buffer_radii_metres]
                                            ).group_by(sq_with_buffers.c.point_id)

        # Return the overall query
        return q_intersections


    def calculate_intersections(self):
        """
        For each sensor location, for each feature:
        extract the UK map geometry for that feature in each of the buffer radii
        """
        # Get all sensors of interest
        q_sensors = self.query_sensor_locations(include_sources=self.sources, with_buffers=True)

        # Iterate over each of the UK map features and calculate the overlap with the sensors
        for feature_type in self.ukmap_features:
            start = time.time()
            self.logger.info("Now working on the %s feature", green(feature_type))

            # Get UKMap geometries for this feature
            q_source = self.query_features(feature_type)

            # Construct one tuple for each sensor, consisting of the point_id and a geometry collection for each radius
            if self.features[feature_type]['type'] == "value":
                select_stmt = self.query_feature_values(feature_type, q_sensors, q_source).subquery().select()
                columns = [c.key for c in IntersectionValues.__table__.columns]
                insert_stmt = insert(IntersectionValues).from_select(columns, select_stmt)
                indexes = [IntersectionValues.point_id, IntersectionValues.feature_type]
                table_name = IntersectionValues.__tablename__
            else:
                select_stmt = self.query_feature_geoms(feature_type, q_sensors, q_source).subquery().select()
                columns = [c.key for c in IntersectionGeoms.__table__.columns]
                insert_stmt = insert(IntersectionGeoms).from_select(columns, select_stmt)
                indexes = [IntersectionGeoms.point_id, IntersectionGeoms.feature_type]
                table_name = IntersectionGeoms.__tablename__

            # Query-and-insert in one statement to reduce local memory overhead and remove database round-trips
            with self.dbcnxn.open_session() as session:
                self.logger.info("Constructing features to merge into database table %s...", green(table_name))
                session.execute(insert_stmt.on_conflict_do_nothing(index_elements=indexes))
                self.logger.info("Finished merging features into database")
                session.commit()

            # Print a final timing message
            self.logger.info("Finished adding records in %s", green(duration(start, time.time())))

    def update_remote_tables(self):
        """Update all remote tables"""
        self.calculate_intersections()

    def query_features(self, feature_name, feature_dict):
        """Query data source, selecting all features matching the requirements in feature_dict.
           Should be implemented by a subsclass"""
        raise NotImplementedError("Subclasses should implement self.query_features")
