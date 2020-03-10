"""
Feature extraction Base  class
"""
import time
from sqlalchemy import func, literal, or_, case, tuple_
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

    def __init__(self, dynamic=False, batch_size=1000, sources=None, **kwargs):
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
        self.sources = sources if sources else []
        self.batch_size = batch_size
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
    def get_static_processed(self, feature_name):
        """Return the features which have already been processed for a given feature name
        
        args:
            feature_name: string
                Name of the feature to check for
        """

        with self.dbcnxn.open_session() as session:
            already_processed_q = session.query(
                StaticFeature.point_id, StaticFeature.feature_name
            ).filter(StaticFeature.feature_name == feature_name)

            return already_processed_q

    @db_query
    def get_dynamic_processed(self, feature_name):
        """Return the features which have already been processed for a given feature name between 
        a start_datetime and end_datetime
        
        args:
            feature_name: string
                Name of the feature to check for
        """

        with self.dbcnxn.open_session() as session:
            already_processed_q = session.query(
                DynamicFeature.point_id, DynamicFeature.feature_name
            ).filter(
                DynamicFeature.feature_name == feature_name,
                DynamicFeature.measurement_start_utc >= self.start_datetime,
                DynamicFeature.measurement_start_utc < self.end_datetime,
            )

            return already_processed_q

    @db_query
    def query_meta_points(self, feature_name, exclude_processed=True):
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

            if exclude_processed:

                preprocessed = self.get_static_processed(feature_name=feature_name).cte(
                    "processed"
                )

                q_meta_point = q_meta_point.filter(
                    ~tuple_(MetaPoint.id, literal(feature_name)).in_(preprocessed)
                )

        return q_meta_point

    @db_query
    def query_features(self, feature_name, feature_type, agg_func, batch_size=1):
        """
        For a given features, produce a query containing the full feature processing stage.

        This avoids complications when trying to work out which interest points have
        already been processed (easy for static features but very complicated for
        dynamic features).

        As we do not filter interest points as part of the query, it will stay the same
        size on repeated calls and can therefore be sliced for batch operations.
        """

        # Get input geometries for this feature
        # self.logger.debug(
        #     "There are %s input geometries to consider",
        #     self.query_input_geometries(feature_name).count(),
        # )
        sq_source = self.query_input_geometries(feature_name, output_type="subquery")

        # Get all the metapoints and buffer geometries as a common table expression
        cte_buffers = self.query_meta_points(
            feature_name=feature_name, limit=batch_size
        ).cte("buffers")

        n_interest_points = self.query_meta_points(
            feature_name=feature_name, output_type="count"
        )

        if n_interest_points == 0:
            self.logger.info(
                "There are 0 interest points left to process for feature %s ...",
                feature_name,
            )
            return None

        # Output about next batch to be processed
        self.logger.info(
            "Preparing to analyse %s interest points of %s unprocessed...",
            green(batch_size),
            green(n_interest_points),
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

            res = (
                session.query(
                    *group_by_columns,
                    value_1000.label("value_1000"),
                    value_500.label("value_500"),
                    value_200.label("value_200"),
                    value_100.label("value_100"),
                    value_10.label("value_10"),
                )
                .join(
                    sq_source,
                    func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_geom_1000),
                )
                .group_by(*group_by_columns)
                .subquery()
            )

            # Left join with coalesce to make sure we always return a value
            out = session.query(
                *group_by_columns,
                literal(feature_name).label("feature_name"),
                func.coalesce(res.c.value_1000, 0.0).label("value_1000"),
                func.coalesce(res.c.value_500, 0.0).label("value_500"),
                func.coalesce(res.c.value_200, 0.0).label("value_200"),
                func.coalesce(res.c.value_100, 0.0).label("value_100"),
                func.coalesce(res.c.value_10, 0.0).label("value_10"),
            ).join(res, cte_buffers.c.id == res.c.id, isouter=True)

            return out

    def update_remote_tables(self):
        """
        For each interest point location, for each feature, extract the geometry for
        that feature in each of the buffer radii then apply the appropriate aggregation
        function to extract a value for each buffer size.
        """
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

            while True:

                # Create full select-and-insert query
                q_select_and_insert = self.query_features(
                    feature_name,
                    feature_type=self.features[feature_name]["type"],
                    agg_func=self.features[feature_name]["aggfunc"],
                    batch_size=self.batch_size,
                    output_type="query",
                )

                if q_select_and_insert:
                    with self.dbcnxn.open_session() as session:
                        self.commit_records(
                            session,
                            q_select_and_insert.subquery(),
                            on_conflict="ignore",
                            table=self.output_table,
                        )
                else:
                    break

                # # Log timing statistics
                # elapsed_seconds = time.time() - insert_start
                # remaining_seconds = elapsed_seconds * (n_batches / idx_batch - 1)
                # self.logger.info(
                #     "Inserted feature records for '%s' [batch %i/%i] after %s (%s remaining)",
                #     feature_name,
                #     idx_batch,
                #     n_batches,
                #     green(duration_from_seconds(elapsed_seconds)),
                #     green(duration_from_seconds(remaining_seconds)),
                # )

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
