"""
Feature extraction Base  class
"""
import math
import time
from sqlalchemy import func, literal, tuple_, or_, case
from sqlalchemy.sql.selectable import Alias as SUBQUERY_TYPE
from ..databases import DBWriter
from ..databases.tables import (
    StaticFeature,
    DynamicFeature,
    UKMap,
    MetaPoint,
)
from ..decorators import db_query
from ..mixins import DBQueryMixin
from ..loggers import duration, green, get_logger, duration_from_seconds


class FeatureExtractor(DBWriter, DBQueryMixin):
    """Extract features which are near to a given set of MetaPoints and inside London"""

    def __init__(self, dynamic=False, sources=[], **kwargs):
        """Base class for extracting features.
        args:
            dynamic: Boolean. Set whether feature is dynamic (e.g. varies over time)
                     Time must always be named measurement_start_utc
        """
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.dynamic = dynamic
        self.sources = sources
        if self.dynamic:
            self.output_table = DynamicFeature
        else:
            self.output_table = StaticFeature

    @property
    def features(self):
        """A dictionary of features of the kind:

        {
            "building_height": {
                "type": "value",
                "feature_dict": {
                    "calculated_height_of_building": ["*"]
                },
                "aggfunc": max_
            }
        }
        """
        raise NotImplementedError("Must be implemented by child classes")

    @property
    def table(self):
        """Either returns an sql table instance or a subquery"""
        raise NotImplementedError("Must be implemented by child classes")

    @db_query
    def query_input_geometries(self, feature_name):
        """Query inputs selecting all input geometries matching the requirements in self.feature_dict"""

        if isinstance(self.table, SUBQUERY_TYPE):
            table = self.table.c
        else:
            table = self.table
        with self.dbcnxn.open_session() as session:
            # Construct column selector for feature
            columns = [table.geom]
            columns = columns + [
                getattr(table, feature)
                for feature in self.features[feature_name]["feature_dict"].keys()
            ]
            if self.dynamic:
                columns = columns + [table.measurement_start_utc]

            q_source = session.query(*columns)

            # Construct filters
            filter_list = []
            if (
                feature_name == "building_height"
            ):  # filter out unreasonably tall buildings from UKMap
                filter_list.append(UKMap.calculated_height_of_building < 999.9)
                filter_list.append(UKMap.feature_type == "Building")
            for column, values in self.features[feature_name]["feature_dict"].items():
                if (len(values) >= 1) and (values[0] != "*"):
                    filter_list.append(
                        or_(*[getattr(table, column) == value for value in values])
                    )
            q_source = q_source.filter(*filter_list)
        return q_source

    @db_query
    def query_meta_points(self):
        """
        Query MetaPoints, selecting all matching sources. We do not filter these in
        order to ensure that repeated calls will return the same set of points.
        """

        boundary_geom = self.query_london_boundary()

        with self.dbcnxn.open_session() as session:

            q_meta_point = session.query(
                MetaPoint.id,
                MetaPoint.source,
                func.Geometry(
                    func.ST_Buffer(func.Geography(MetaPoint.location), 1000)
                ).label("buff_geom_1000"),
                func.Geometry(
                    func.ST_Buffer(func.Geography(MetaPoint.location), 500)
                ).label("buff_geom_500"),
                func.Geometry(
                    func.ST_Buffer(func.Geography(MetaPoint.location), 200)
                ).label("buff_geom_200"),
                func.Geometry(
                    func.ST_Buffer(func.Geography(MetaPoint.location), 100)
                ).label("buff_geom_100"),
                func.Geometry(
                    func.ST_Buffer(func.Geography(MetaPoint.location), 10)
                ).label("buff_geom_10"),
            ).filter(MetaPoint.location.ST_Within(boundary_geom))

            if self.sources:
                self.logger.debug(
                    "Restricting to interest points from %s", self.sources
                )
                q_meta_point = q_meta_point.filter(MetaPoint.source.in_(self.sources))

        return q_meta_point

    @db_query
    def query_features(self, feature_name, feature_type, agg_func):
        """
        For a given features, produce a query containing the full feature processing stage.

        This avoids complications when trying to work out which interest points have
        already been processed (easy for static features but very complicated for
        dynamic features).

        As we do not filter interest points as part of the query, it will stay the same
        size on repeated calls and can therefore be sliced for batch operations.
        """

        # Get input geometries for this feature
        self.logger.debug(
            "There are %s input geometries to consider",
            self.query_input_geometries(feature_name).count(),
        )
        sq_source = self.query_input_geometries(feature_name, output_type="subquery")

        # Get all the metapoints and buffer geometries as a common table expression
        cte_buffers = self.query_meta_points().cte("buffers")
        self.logger.debug(
            "There are %s interest points to consider", self.query_meta_points().count()
        )

        # Output about next batch to be processed
        self.logger.info(
            "Preparing to analyse interest points for feature %s", green(feature_name),
        )

        if feature_type == "geom":
            # Use case to avoid calculating intersections if we know the geom is covered
            # by the buffer (see https://postgis.net/2014/03/14/tip_intersection_faster/)
            value_1000 = agg_func(
                case(
                    [
                        (
                            func.ST_CoveredBy(
                                sq_source.c.geom, cte_buffers.c.buff_geom_1000
                            ),
                            sq_source.c.geom,
                        ),
                    ],
                    else_=func.ST_Intersection(
                        sq_source.c.geom, cte_buffers.c.buff_geom_1000
                    ),
                )
            )
            value_500 = agg_func(
                case(
                    [
                        (
                            func.ST_CoveredBy(
                                sq_source.c.geom, cte_buffers.c.buff_geom_500
                            ),
                            sq_source.c.geom,
                        ),
                    ],
                    else_=func.ST_Intersection(
                        sq_source.c.geom, cte_buffers.c.buff_geom_500
                    ),
                )
            )
            value_200 = agg_func(
                case(
                    [
                        (
                            func.ST_CoveredBy(
                                sq_source.c.geom, cte_buffers.c.buff_geom_200
                            ),
                            sq_source.c.geom,
                        ),
                    ],
                    else_=func.ST_Intersection(
                        sq_source.c.geom, cte_buffers.c.buff_geom_200
                    ),
                )
            )
            value_100 = agg_func(
                case(
                    [
                        (
                            func.ST_CoveredBy(
                                sq_source.c.geom, cte_buffers.c.buff_geom_100
                            ),
                            sq_source.c.geom,
                        ),
                    ],
                    else_=func.ST_Intersection(
                        sq_source.c.geom, cte_buffers.c.buff_geom_100
                    ),
                )
            )
            value_10 = agg_func(
                case(
                    [
                        (
                            func.ST_CoveredBy(
                                sq_source.c.geom, cte_buffers.c.buff_geom_10
                            ),
                            sq_source.c.geom,
                        ),
                    ],
                    else_=func.ST_Intersection(
                        sq_source.c.geom, cte_buffers.c.buff_geom_10
                    ),
                )
            )

        elif feature_type == "value":
            # If this is a value, there should only be one key
            _value_column = list(self.features[feature_name]["feature_dict"].keys())[0]
            value_1000 = agg_func(getattr(sq_source.c, _value_column)).filter(
                func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_geom_1000)
            )
            value_500 = agg_func(getattr(sq_source.c, _value_column)).filter(
                func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_geom_500)
            )
            value_200 = agg_func(getattr(sq_source.c, _value_column)).filter(
                func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_geom_200)
            )
            value_100 = agg_func(getattr(sq_source.c, _value_column)).filter(
                func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_geom_100)
            )
            value_10 = agg_func(getattr(sq_source.c, _value_column)).filter(
                func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_geom_10)
            )

        else:
            raise TypeError("{} is not a feature type".format(feature_type))

        with self.dbcnxn.open_session() as session:
            # Set the list of columns that we will group by
            group_by_columns = [cte_buffers.c.id]
            if self.dynamic:
                group_by_columns.append(sq_source.c.measurement_start_utc)

            # Do a spatial outer-join between the q_source and q_meta_point on
            # intersections, which means that we only join if the geometries intersect.
            # Use coalesce to make sure we return 0 if there is no value
            return (
                session.query(
                    *group_by_columns,
                    literal(feature_name).label("feature_name"),
                    func.coalesce(value_1000, 0.0).label("value_1000"),
                    func.coalesce(value_500, 0.0).label("value_500"),
                    func.coalesce(value_200, 0.0).label("value_200"),
                    func.coalesce(value_100, 0.0).label("value_100"),
                    func.coalesce(value_10, 0.0).label("value_10"),
                )
                .join(
                    sq_source,
                    func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_geom_1000),
                )
                .group_by(*group_by_columns)
            )

    def update_remote_tables(self):
        """
        For each interest point location, for each feature, extract the geometry for
        that feature in each of the buffer radii then apply the appropriate aggregation
        function to extract a value for each buffer size.
        """
        batch_size = 1000
        update_start = time.time()

        # Iterate over each of the features and calculate the overlap with the interest points
        n_features = len(self.features)
        for idx_feature, feature_name in enumerate(self.features, start=1):
            feature_start = time.time()
            self.logger.info(
                "Now working on the %s feature [feature %i/%i]",
                green(feature_name),
                idx_feature,
                n_features,
            )

            # Create full select-and-insert query
            q_select_and_insert = self.query_features(
                feature_name,
                feature_type=self.features[feature_name]["type"],
                agg_func=self.features[feature_name]["aggfunc"],
            )

            # Count how many records will be inserted here
            self.logger.debug(
                "Determining how many records will need to be inserted..."
            )
            n_records = q_select_and_insert.count()
            n_batches = round(0.5 + n_records / batch_size)

            # Slice the main query into batches, inserting each one in turn
            self.logger.info(
                "Preparing to insert %s feature records in batches of %i...",
                green(n_records),
                batch_size,
            )
            for idx_batch, batch_start in enumerate(
                range(0, n_records, batch_size), start=1
            ):
                batch_stop = min(batch_start + batch_size, n_records)
                self.logger.info(
                    "Inserting %i feature records for %s [batch %i/%i]...",
                    batch_stop - batch_start,
                    feature_name,
                    idx_batch,
                    n_batches,
                )
                q_batch_insert = q_select_and_insert.slice(batch_start, batch_stop)

                # Query-and-insert in one statement to reduce local memory overhead and
                # remove database round-trips
                with self.dbcnxn.open_session() as session:
                    self.commit_records(
                        session,
                        q_batch_insert.subquery(),
                        table=self.output_table,
                        on_conflict="ignore",
                    )

                # Log timing statistics
                elapsed_seconds = time.time() - feature_start
                remaining_seconds = elapsed_seconds * (n_batches / idx_batch - 1)
                self.logger.info(
                    "Inserted '%s' records [batch %i/%i] after %s (%s remaining)",
                    feature_name,
                    idx_batch,
                    n_batches,
                    green(duration_from_seconds(elapsed_seconds)),
                    green(duration_from_seconds(remaining_seconds)),
                )

            # Print a timing message at the end of each feature
            self.logger.info(
                "Finished adding records for '%s' after %s",
                feature_name,
                green(duration(feature_start, time.time())),
            )

        # Print a final timing message
        self.logger.info(
            "Finished adding records after %s",
            green(duration(update_start, time.time())),
        )
