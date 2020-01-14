"""
Feature extraction Base  class
"""
import time
from sqlalchemy import func, literal, tuple_, or_
from sqlalchemy.sql.selectable import Alias as SUBQUERY_TYPE
from ..databases import DBWriter
from ..databases.tables import (IntersectionGeom, IntersectionValue, IntersectionValueDynamic,
                                LondonBoundary, MetaPoint, UKMap)
from ..loggers import duration, green, get_logger


class Features(DBWriter):
    """Extract features which are near to a given set of MetaPoints and inside London"""

    def __init__(self, **kwargs):
        """Base class for extracting features.
        args:
            dynamic: Boolean. Set whether feature is dynamic (e.g. varies over time)
                     Time must always be named measurement_start_utc
        """

        self.sources = kwargs.pop("sources", [])

        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        # Radius around each interest point used for feature extraction.
        # Changing these would require redefining the database schema
        self.buffer_radii_metres = [1000, 500, 200, 100, 10]
        self.dynamic = False

    @property
    def features(self):
        """A dictionary of features of the kind:

        {"building_height": {"type": "value", "feature_dict": {"calculated_height_of_building": ["*"]},
                                "aggfunc": max_}
        }
        """
        raise NotImplementedError("Must be implemented by child classes")

    @property
    def table(self):
        """Either returns an sql table instance or a subquery"""
        raise NotImplementedError("Must be implemented by child classes")

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

    def query_features(self, feature_name):
        """Query features selecting all features matching the requirements in self.feature_dict"""

        if isinstance(self.table, SUBQUERY_TYPE):
            table = self.table.c
        else:
            table = self.table
        with self.dbcnxn.open_session() as session:
            # Construct column selector for feature
            columns = [table.geom]
            columns = columns + [getattr(table, feature)
                                 for feature in self.features[feature_name]['feature_dict'].keys()]
            if self.dynamic:
                columns = columns + [table.measurement_start_utc]

            q_source = session.query(*columns)
            # Construct filters
            filter_list = []
            if feature_name == "building_height":  # filter out unreasonably tall buildings from UKMap
                filter_list.append(UKMap.calculated_height_of_building < 999.9)
                filter_list.append(UKMap.feature_type == 'Building')
            for column, values in self.features[feature_name]["feature_dict"].items():
                if (len(values) == 1) and (values[0] != '*'):
                    filter_list.append(or_(*[getattr(table, column) == value for value in values]))
            q_source = q_source.filter(*filter_list)
        return q_source

    def query_feature_geoms(self, feature_name, q_metapoints, q_geometries):
        """Construct one record for each interest point containing the point ID and one geometry column per buffer"""

        with self.dbcnxn.open_session() as session:
            # Cross join interest point and geometry queries...
            sq_metapoints = q_metapoints.subquery()
            sq_geometries = q_geometries.subquery()

            # ... restrict to only those within max(radius) of one another
            # ... construct a column for each radius, containing the intersection with each geometry
            # => [M < Npoints * Ngeometries records]
            intersection_columns = [func.ST_Intersection(getattr(sq_metapoints.c, str(radius)),
                                                         sq_geometries.c.geom).label("intst_{}".format(radius))
                                    for radius in self.buffer_radii_metres]

            intersection_filter_columns = [func.ST_Intersects(getattr(sq_metapoints.c, str(radius)),
                                                              sq_geometries.c.geom).
                                           label("intersects_{}".format(radius))
                                           for radius in self.buffer_radii_metres]

            sq_within = session.query(sq_metapoints,
                                      sq_geometries,
                                      *intersection_columns,
                                      *intersection_filter_columns,
                                      ).filter(func.ST_Intersects(getattr(sq_metapoints.c,
                                                                          str(max(self.buffer_radii_metres))),
                                                                  sq_geometries.c.geom)).subquery()

            # Group these by interest point, unioning geometries: [Npoints records]
            q_intersections = session.query(sq_within.c.id,
                                             literal(feature_name).label("feature_name"),
                                             *[func.ST_ForceCollection(
                                                 func.ST_Collect(getattr(sq_within.c, "intst_{}".format(radius)))
                                                 .filter(getattr(sq_within.c, "intersects_{}".format(radius)))
                                             ).label("geom_{}".format(radius))
                                                 for radius in self.buffer_radii_metres]
                                             ).group_by(sq_within.c.id) #.subquery()

        #     # Join with meta points to ensure every meta point gets an entry,
        #     # even if there is no intersection in the buffer
        #     q_intersections = session.query(sq_metapoints.c.id,
        #                                     literal(feature_name).label("feature_name"),
        #                                     *[getattr(sq_intersections.c, "geom_{}".format(radius))
        #                                       for radius in self.buffer_radii_metres]
        #                                     ).join(sq_intersections,
        #                                            sq_intersections.c.id == sq_metapoints.c.id, isouter=True)

        # print(sq_intersections.statement.compile(compile_kwargs={"literal_binds": True}))
        # quit()

        # Return the overall query
        return q_intersections

    def query_feature_values(self, feature_name, q_metapoints, q_geometries):
        """Construct one record for each interest point containing the point ID and one value column per buffer"""

        agg_func = self.features[feature_name]['aggfunc']
        # If its a value, there should only be one key
        value_column = list(self.features[feature_name]["feature_dict"].keys())[0]

        with self.dbcnxn.open_session() as session:
            # Cross join interest point and geometry queries...
            sq_metapoints = q_metapoints.subquery()
            sq_geometries = q_geometries.subquery()

            # ... restrict to only those within max(radius) of one another
            # ... construct a column for each radius, containing building height if the building is inside that radius
            # => [M < Npoints * Ngeometries records]
            intersection_columns = [func.ST_Intersection(getattr(sq_metapoints.c, str(radius)),
                                                         sq_geometries.c.geom).label("intst_{}".format(radius))
                                    for radius in self.buffer_radii_metres]

            intersection_filter_columns = [func.ST_Intersects(getattr(sq_metapoints.c, str(radius)),
                                                              sq_geometries.c.geom)
                                           .label("intersects_{}".format(radius))
                                           for radius in self.buffer_radii_metres]

            sq_within = session.query(sq_metapoints,
                                      sq_geometries,
                                      *intersection_columns,
                                      *intersection_filter_columns
                                      ).filter(func.ST_Intersects(getattr(sq_metapoints.c,
                                                                          str(max(self.buffer_radii_metres))),
                                                                  sq_geometries.c.geom)
                                               ).subquery()

            # Now group these by interest point, aggregating the height columns using the maximum in each group
            # => [Npoints records]
            aggregate_funcs = [
                func.coalesce(agg_func(getattr(sq_within.c,
                                               value_column)).filter(getattr(sq_within.c,
                                                                             "intersects_{}".format(radius))), 0.0)
                .label("value_{}".format(radius))
                for radius in self.buffer_radii_metres
            ]

            if self.dynamic:
                q_intersections = session.query(sq_within.c.id,
                                                literal(feature_name).label("feature_name"),
                                                sq_within.c.measurement_start_utc,
                                                *aggregate_funcs
                                                ).group_by(sq_within.c.id, sq_within.c.measurement_start_utc) \
                                                 .order_by(sq_within.c.id, sq_within.c.measurement_start_utc)

            else:
                sq_intersections = session.query(sq_within.c.id,
                                                 literal(feature_name).label("feature_name"),
                                                 *aggregate_funcs
                                                 ).group_by(sq_within.c.id).subquery()

                # Join with meta points to ensure every meta point gets an entry,
                # even if there is no intersection in the buffer
                q_intersections = session.query(sq_metapoints.c.id,
                                                literal(feature_name).label("feature_name"),
                                                *[func.coalesce(getattr(sq_intersections.c, "value_{}".format(radius)), 0.0)
                                                  for radius in self.buffer_radii_metres]
                                                ).join(sq_intersections,
                                                       sq_intersections.c.id == sq_metapoints.c.id,
                                                       isouter = True)

        # Return the overall query
        return q_intersections

    def process_value_features(self, feature_name, q_metapoints, q_source):
        """
        Process value features in batches since some of them are extremely slow
        (and they need to be independentely calculated for each interest point anyway)
        """
        # Filter out any that have already been calculated
        with self.dbcnxn.open_session() as session:
            sq_intersection_value=session.query(IntersectionValue.point_id, IntersectionValue.feature_name).subquery()
        q_filtered=q_metapoints.filter(~tuple_(MetaPoint.id, literal(feature_name)).in_(sq_intersection_value))

        n_interest_points=q_filtered.count()
        batch_size=10
        self.logger.info("Preparing to analyse %s interest points in batches of %i...",
                         green(n_interest_points), batch_size)

        # Iterate over interest points in batches, yielding the insert statement at each step
        for idx, _ in enumerate(range(0, n_interest_points, batch_size), start=1):
            self.logger.info("Calculating %s for next %i interest points [batch %i/%i]...",
                             feature_name, batch_size, idx, round(0.5 + n_interest_points / batch_size))
            q_batch = q_filtered.slice(0, batch_size)
            select_stmt = self.query_feature_values(feature_name, q_batch, q_source).subquery()
            yield select_stmt

    def process_geom_features(self, feature_name, q_metapoints, q_source):
        """
        Process geometric features in large batches as none of them are particularly slow at present
        (and they need to be independentely calculated for each interest point anyway)
        """
        # Filter out any that have already been calculated
        with self.dbcnxn.open_session() as session:
            sq_intersection_geom = session.query(IntersectionGeom.point_id, IntersectionGeom.feature_name).subquery()
        q_filtered = q_metapoints.filter(~tuple_(MetaPoint.id, literal(feature_name)).in_(sq_intersection_geom))

        self.logger.debug("Processing the following interest points: %s", [str(i.id) for i in q_filtered.all()])
        n_interest_points = q_filtered.count()
        batch_size = 10
        self.logger.info("Preparing to analyse %s interest points in batches of %i...",
                         green(n_interest_points), batch_size)

        # Iterate over interest points in batches, yielding the insert statement at each step
        for idx, _ in enumerate(range(0, n_interest_points, batch_size), start=1):
            self.logger.info("Calculating %s for next %i interest points [batch %i/%i]...",
                             feature_name, batch_size, idx, round(0.5 + n_interest_points / batch_size))
            q_batch = q_filtered.slice(0, batch_size)
            select_stmt = self.query_feature_geoms(feature_name, q_batch, q_source).subquery()
            yield select_stmt

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
                q_metapoints = self.query_meta_points(include_sources=self.sources, with_buffers=True)
                for select_stmt in self.process_value_features(feature_name, q_metapoints, q_source):
                    with self.dbcnxn.open_session() as session:
                        if self.dynamic:
                            self.commit_records(session, select_stmt, table=IntersectionValueDynamic,
                                                on_conflict_do_nothing=True)
                        else:
                            self.commit_records(session, select_stmt, table=IntersectionValue,
                                                on_conflict_do_nothing=True)
            else:
                q_metapoints = self.query_meta_points(include_sources=self.sources, with_buffers=True)
                for select_stmt in self.process_geom_features(feature_name, q_metapoints, q_source):
                    with self.dbcnxn.open_session() as session:
                        self.commit_records(session, select_stmt, table=IntersectionGeom,
                                            on_conflict_do_nothing=True)

            # Print a final timing message
            self.logger.info("Finished adding records after %s", green(duration(feature_start, time.time())))

    def aggregate_geom_features(self):
        """Apply aggregation functions to the intersected geometries and insert into the model output table"""
        for feature_name in self.features:
            feature_start = time.time()
            if self.features[feature_name]["type"] == "geom":
                self.logger.info("Now applying aggregation function on the %s feature", green(feature_name))
                agg_func = self.features[feature_name]['aggfunc']
                query_args = [agg_func(getattr(IntersectionGeom, 'geom_' + str(radius))).label('value_' + str(radius))
                              for radius in self.buffer_radii_metres]
                with self.dbcnxn.open_session() as session:

                    select_stmt = session.query(IntersectionGeom.point_id,
                                                literal(feature_name).label("feature_name"),
                                                *query_args
                                                ).filter(IntersectionGeom.feature_name == feature_name).group_by(
                                                    IntersectionGeom.point_id).subquery()

                    self.commit_records(session, select_stmt, table=IntersectionValue, on_conflict_do_nothing=True)

            # Print a final timing message
            self.logger.info("Finished adding records after %s", green(duration(feature_start, time.time())))

    def update_remote_tables(self):
        """Update all remote tables"""
        self.calculate_intersections()
        self.aggregate_geom_features()
