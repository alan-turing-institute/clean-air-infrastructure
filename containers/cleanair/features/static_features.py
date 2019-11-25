"""
Feature extraction Base  class
"""
import time
from sqlalchemy import func, literal, tuple_
from sqlalchemy.dialects.postgresql import insert
from ..databases import DBWriter
from ..databases.tables import IntersectionGeom, IntersectionValue, LondonBoundary, MetaPoint
from ..loggers import duration, green
import pandas as pd
pd.set_option('display.max_rows', 50000)
class StaticFeatures(DBWriter):
    """Extract features which are near to a given set of MetaPoints and inside London"""
    def __init__(self, **kwargs):
        self.sources = kwargs.pop("sources", [])

        # Initialise parent classes
        super().__init__(**kwargs)

        # Radius around each interest point used for feature extraction.
        # Changing these would require redefining the database schema
        self.buffer_radii_metres = [1000, 500, 200, 100, 10]

        # Define in inhereting classes
        self.features = None

    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London"""
        with self.dbcnxn.open_session() as session:
            hull = session.scalar(func.ST_ConvexHull(func.ST_Collect(LondonBoundary.geom)))
        return hull

    def query_meta_points(self, include_sources=None, with_buffers=False):
        """Query MetaPoints, selecting all matching include_sources"""
        boundary_geom = self.query_london_boundary()
        with self.dbcnxn.open_session() as session:
            columns = [MetaPoint.id]
            if with_buffers:
                columns += [func.Geometry(func.ST_Buffer(func.Geography(MetaPoint.location), rad)).label(str(rad))
                            for rad in self.buffer_radii_metres]
            _query = session.query(*columns).filter(MetaPoint.location.ST_Within(boundary_geom))
            if include_sources:
                _query = _query.filter(MetaPoint.source.in_(include_sources))
        return _query

    def query_feature_geoms(self, feature_name, q_metapoints, q_geometries):
        """Construct one record for each interest point containing the point ID and one geometry column per buffer"""

        with self.dbcnxn.open_session() as session:
            # Cross join interest point and geometry queries...
            sq_metapoints = q_metapoints.limit(10).subquery()
            sq_geometries = q_geometries.subquery()

            
            # ... restrict to only those within max(radius) of one another
            # ... construct a column for each radius, containing the intersection with each geometry
            # => [M < Npoints * Ngeometries records]
            intersection_columns = [func.ST_Intersection(getattr(sq_metapoints.c, str(radius)),
                                                         sq_geometries.c.geom).label("intst_{}".format(radius)) for radius in self.buffer_radii_metres]

            intersection_filter_columns = [func.ST_Intersects(getattr(sq_metapoints.c, str(radius)),
                                                         sq_geometries.c.geom).label("intersects_{}".format(radius)) for radius in self.buffer_radii_metres]

            sq_within = session.query(sq_metapoints,
                                      sq_geometries,
                                      *intersection_columns,
                                      *intersection_filter_columns,
                                      ).filter(func.ST_Intersects(getattr(sq_metapoints.c, str(max(self.buffer_radii_metres))),
                                                               sq_geometries.c.geom)).subquery()

            # # Group these by interest point, unioning geometries: [Npoints records]
            q_intersections = session.query(sq_within.c.id,
                                            literal(feature_name).label("feature_name"),
                                            *[func.ST_ForceCollection(
                                                func.ST_Collect(getattr(sq_within.c, "intst_{}".format(radius))).filter(getattr(sq_within.c, "intersects_{}".format(radius)))
                                                ).label("geom_{}".format(radius))
                                              for radius in self.buffer_radii_metres]
                                            ).group_by(sq_within.c.id)


        # Return the overall query
        return q_intersections

    def process_value_features(self, feature_name, q_metapoints, q_source):
        """
        Process value features in batches since some of them are extremely slow
        (and they need to be independentely calculated for each interest point anyway)
        """
        # Filter out any that have already been calculated
        with self.dbcnxn.open_session() as session:
            sq_intersection_value = session.query(IntersectionValue.point_id, IntersectionValue.feature_name).subquery()
        q_filtered = q_metapoints.filter(~tuple_(MetaPoint.id, literal(feature_name)).in_(sq_intersection_value))

        n_interest_points = q_filtered.count()
        batch_size = 10
        self.logger.info("Preparing to analyse %s interest points in batches of %i...",
                         green(n_interest_points), batch_size)

        # Iterate over interest points in batches, yielding the insert statement at each step
        for idx, batch_start in enumerate(range(0, n_interest_points, batch_size), start=1):
            batch_stop = min(batch_start + batch_size, n_interest_points)
            self.logger.info("Calculating %s for next %i interest points [batch %i/%i]...",
                             feature_name, batch_stop - batch_start, idx, round(0.5 + n_interest_points / batch_size))
            q_batch = q_filtered.slice(batch_start, batch_stop)
            select_stmt = self.query_feature_values(feature_name, q_batch, q_source).subquery().select()
            columns = [c.key for c in IntersectionValue.__table__.columns]
            insert_stmt = insert(IntersectionValue).from_select(columns, select_stmt)
            indexes = [IntersectionValue.point_id, IntersectionValue.feature_name]
            yield (insert_stmt, indexes)

    def process_geom_features(self, feature_name, q_metapoints, q_source):
        """
        Process geometric features in large batches as none of them are particularly slow at present
        (and they need to be independentely calculated for each interest point anyway)
        """
        # Filter out any that have already been calculated
        with self.dbcnxn.open_session() as session:
            sq_intersection_geom = session.query(IntersectionGeom.point_id, IntersectionGeom.feature_name).subquery()
        q_filtered = q_metapoints.filter(~tuple_(MetaPoint.id, literal(feature_name)).in_(sq_intersection_geom))

        n_interest_points = q_filtered.count()
        batch_size = 1000
        self.logger.info("Preparing to analyse %s interest points in batches of %i...",
                         green(n_interest_points), batch_size)

        # Iterate over interest points in batches, yielding the insert statement at each step
        for idx, batch_start in enumerate(range(0, n_interest_points, batch_size), start=1):
            batch_stop = min(batch_start + batch_size, n_interest_points)
            self.logger.info("Calculating %s for next %i interest points [batch %i/%i]...",
                             feature_name, batch_stop - batch_start, idx, round(0.5 + n_interest_points / batch_size))
            q_batch = q_filtered.slice(batch_start, batch_stop)
            select_stmt = self.query_feature_geoms(feature_name, q_batch, q_source).subquery().select()
            columns = [c.key for c in IntersectionGeom.__table__.columns]
            insert_stmt = insert(IntersectionGeom).from_select(columns, select_stmt)
            indexes = [IntersectionGeom.point_id, IntersectionGeom.feature_name]
            yield (insert_stmt, indexes)

    def insert_records(self, insert_stmt, indexes, table_name):
        """Query-and-insert in one statement to reduce local memory overhead and remove database round-trips"""
        start = time.time()
        self.logger.info("Constructing features to merge into database table %s...", green(table_name))
        with self.dbcnxn.open_session() as session:
            session.execute(insert_stmt.on_conflict_do_nothing(index_elements=indexes))
            session.commit()
        self.logger.info("Finished merging feature batch into database after %s", green(duration(start, time.time())))

    def calculate_intersections(self):
        """
        For each interest point location, for each feature:
        extract the geometry for that feature in each of the buffer radii
        """
        # Iterate over each of the features and calculate the overlap with the interest points
        for feature_name in self.features:
            feature_start = time.time()
            self.logger.info("Now working on the %s feature", green(feature_name))

            # Get geometries for this feature
            q_source = self.query_features(feature_name)

            # Construct one tuple for each interest point: the id and a geometry collection for each radius
            # Query-and-insert in one statement to reduce local memory overhead and remove database round-trips
            if self.features[feature_name]["type"] == "value":
                q_metapoints = self.query_meta_points(include_sources=self.sources)
                for insert_stmt, indexes in self.process_value_features(feature_name, q_metapoints, q_source):
                    self.insert_records(insert_stmt, indexes, IntersectionValue.__tablename__)
            else:
                q_metapoints = self.query_meta_points(include_sources=self.sources, with_buffers=True)
                for insert_stmt, indexes in self.process_geom_features(feature_name, q_metapoints, q_source):
                    self.insert_records(insert_stmt, indexes, IntersectionGeom.__tablename__)

            # Print a final timing message
            self.logger.info("Finished adding records after %s", green(duration(feature_start, time.time())))

    def aggregate_geom_features(self):
        """Apply aggregation functions to the intersected geometries and insert into the model output table"""
        for feature_name in self.features:
            feature_start = time.time()
            if self.features[feature_name]["type"] == "geom":
                self.logger.info("Now working on the %s feature", green(feature_name))
                agg_func = self.features[feature_name]['aggfunc']
                query_args = [agg_func(getattr(IntersectionGeom, 'geom_' + str(radius))).label('value_' + str(radius))
                              for radius in self.buffer_radii_metres]
                with self.dbcnxn.open_session() as session:

                    select_stmt = session.query(IntersectionGeom.point_id,
                                                literal(feature_name).label("feature_name"),
                                                *query_args
                                                ).filter(IntersectionGeom.feature_name == feature_name).group_by(
                                                    IntersectionGeom.point_id)

                    select_stmt = select_stmt.subquery().select()
                    columns = [c.key for c in IntersectionValue.__table__.columns]
                    insert_stmt = insert(IntersectionValue).from_select(columns, select_stmt)
                    indexes = [IntersectionValue.point_id, IntersectionValue.feature_name]
                    self.insert_records(insert_stmt, indexes, IntersectionValue.__tablename__)

            # Print a final timing message
            self.logger.info("Finished adding records after %s", green(duration(feature_start, time.time())))

    def update_remote_tables(self):
        """Update all remote tables"""
        self.calculate_intersections()
        self.aggregate_geom_features()

    def query_features(self, feature_name):
        """Query data source, selecting all features matching the requirements in feature_dict.
           Should be implemented by a subsclass"""
        raise NotImplementedError("Subclasses should implement self.query_features")

    def query_feature_values(self, feature_name, q_metapoints, q_geometries):
        """Construct one record for each interest point containing the point ID and one value column per buffer"""
        raise NotImplementedError("Subclasses should implement self.query_feature_values")
