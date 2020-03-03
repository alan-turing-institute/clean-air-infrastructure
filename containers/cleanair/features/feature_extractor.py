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
from ..loggers import duration, green, get_logger


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
    def query_meta_points(self):
        """Query MetaPoints, selecting all matching sources"""

        boundary_geom = self.query_london_boundary()

        with self.dbcnxn.open_session() as session:

            q_meta_point = session.query(
                MetaPoint.id,
                MetaPoint.source,
                func.Geometry(
                    func.ST_Buffer(func.Geography(MetaPoint.location), 1000)
                ).label("buff_1000"),
                func.Geometry(
                    func.ST_Buffer(func.Geography(MetaPoint.location), 500)
                ).label("buff_500"),
                func.Geometry(
                    func.ST_Buffer(func.Geography(MetaPoint.location), 200)
                ).label("buff_200"),
                func.Geometry(
                    func.ST_Buffer(func.Geography(MetaPoint.location), 100)
                ).label("buff_100"),
                func.Geometry(
                    func.ST_Buffer(func.Geography(MetaPoint.location), 10)
                ).label("buff_10"),
            ).filter(MetaPoint.location.ST_Within(boundary_geom))

            if self.sources:
                self.logger.debug("Restricting to interest points from %s", self.sources)
                q_meta_point = q_meta_point.filter(
                    MetaPoint.source.in_(self.sources)
                )

            # # Dynamic features cannot exclude metapoints just based on whether they
            # # exist in the output table, since they may not exist for the relevant time
            # # period
            # if exclude_processed and (not self.dynamic):
            #     already_processed_sq = (
            #         session.query(
            #             self.output_table.point_id, self.output_table.feature_name
            #         )
            #         .filter(self.output_table.feature_name == feature_name)
            #         .subquery()
            #     )

            #     q_meta_point = q_meta_point.filter(
            #         ~tuple_(MetaPoint.id, literal(feature_name)).in_(
            #             already_processed_sq
            #         )
            #     )

        return q_meta_point

    @db_query
    def query_features(self, feature_name):
        """Query features selecting all features matching the requirements in self.feature_dict"""

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

    def process_features(self, feature_name, feature_type, agg_func):
        """
        Process each feature as a single batch. This avoids complications when trying to
        work out which interest points have already been processed (easy for static
        features but very complicated for dynamic features). This increases the costs of
        each database transaction but minimises the number of transactions.
        """

        # Get geometries for this feature
        print("Get geometries for this feature")
        sq_source = self.query_features(feature_name, output_type="subquery")

        # Get all the metapoints and buffer geometries as a common table expression
        print("Get all the metapoints and buffer geometries as a common table expression")
        cte_buffers = self.query_meta_points().cte("buffers")

        # print("There are", cte_buffers.count(), "interest points")

        # # Check whether there are points left to process in a batch
        # print("Check whether there are points left to process in a batch")
        # n_interest_points = self.query_meta_points(
        #     sources=self.sources, feature_name=feature_name, output_type="count"
        # )
        # print("There are", n_interest_points)
        # if n_interest_points == 0:
        #     return None
        # self.logger.info(
        #     "There are %s interest points left to process for feature %s ...",
        #     green(n_interest_points),
        #     green(feature_name),
        # )

        # Output about next batch to be processed
        print("Output about next batch to be processed")
        self.logger.info(
            "Preparing to analyse interest points for feature %s",
            green(feature_name),
        )

        if feature_type == "geom":
            print("Processing a geometry-based feature")
            # Use case to avoid calculating intersection if we know
            # the geom is covered by the buffer (see https://postgis.net/2014/03/14/tip_intersection_faster/)
            value_1000 = agg_func(
                case(
                    [
                        (
                            func.ST_CoveredBy(
                                sq_source.c.geom, cte_buffers.c.buff_1000
                            ),
                            sq_source.c.geom,
                        ),
                    ],
                    else_=func.ST_Intersection(
                        sq_source.c.geom, cte_buffers.c.buff_1000
                    ),
                )
            )
            value_500 = agg_func(
                case(
                    [
                        (
                            func.ST_CoveredBy(sq_source.c.geom, cte_buffers.c.buff_500),
                            sq_source.c.geom,
                        ),
                    ],
                    else_=func.ST_Intersection(
                        sq_source.c.geom, cte_buffers.c.buff_500
                    ),
                )
            )
            value_200 = agg_func(
                case(
                    [
                        (
                            func.ST_CoveredBy(sq_source.c.geom, cte_buffers.c.buff_200),
                            sq_source.c.geom,
                        ),
                    ],
                    else_=func.ST_Intersection(
                        sq_source.c.geom, cte_buffers.c.buff_200
                    ),
                )
            )
            value_100 = agg_func(
                case(
                    [
                        (
                            func.ST_CoveredBy(sq_source.c.geom, cte_buffers.c.buff_100),
                            sq_source.c.geom,
                        ),
                    ],
                    else_=func.ST_Intersection(
                        sq_source.c.geom, cte_buffers.c.buff_100
                    ),
                )
            )
            value_10 = agg_func(
                case(
                    [
                        (
                            func.ST_CoveredBy(sq_source.c.geom, cte_buffers.c.buff_10),
                            sq_source.c.geom,
                        ),
                    ],
                    else_=func.ST_Intersection(sq_source.c.geom, cte_buffers.c.buff_10),
                )
            )

        elif feature_type == "value":
            print("Processing a value-based feature")
            # If its a value, there should only be one key
            value_column = list(self.features[feature_name]["feature_dict"].keys())[0]
            value_1000 = agg_func(getattr(sq_source.c, value_column)).filter(
                func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_1000)
            )
            value_500 = agg_func(getattr(sq_source.c, value_column)).filter(
                func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_500)
            )
            value_200 = agg_func(getattr(sq_source.c, value_column)).filter(
                func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_200)
            )
            value_100 = agg_func(getattr(sq_source.c, value_column)).filter(
                func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_100)
            )
            value_10 = agg_func(getattr(sq_source.c, value_column)).filter(
                func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_10)
            )

        else:
            raise TypeError("{} is not a feature type".format(feature_type))

        with self.dbcnxn.open_session() as session:
            print("Constructing the query")

            # Set the list of columns that we will group by
            group_by_columns = [cte_buffers.c.id]
            if self.dynamic:
                group_by_columns.append(sq_source.c.measurement_start_utc)

            q_result = session.query(
                *group_by_columns,
                value_1000.label("value_1000"),
                value_500.label("value_500"),
                value_200.label("value_200"),
                value_100.label("value_100"),
                value_10.label("value_10"),
            )

            sq_result = (
                q_result.join(
                    sq_source,
                    func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_1000),
                )
                .group_by(*group_by_columns)
                .subquery()
            )

            # Left join with coalesce to make sure we always return a value
            return session.query(
                *group_by_columns,
                literal(feature_name).label("feature_name"),
                func.coalesce(sq_result.c.value_1000, 0.0).label("value_1000"),
                func.coalesce(sq_result.c.value_500, 0.0).label("value_500"),
                func.coalesce(sq_result.c.value_200, 0.0).label("value_200"),
                func.coalesce(sq_result.c.value_100, 0.0).label("value_100"),
                func.coalesce(sq_result.c.value_10, 0.0).label("value_10"),
            ).join(sq_result, cte_buffers.c.id == sq_result.c.id, isouter=True)

    def update_remote_tables(self):
        """
        For each interest point location, for each feature:
        extract the geometry for that feature in each of the buffer radii
        """
        # Iterate over each of the features and calculate the overlap with the interest points
        for idx, feature_name in enumerate(self.features, start=1):
            feature_start = time.time()
            print("testing debug message")
            self.logger.info(
                "Now working on the %s feature [feature %i/%i]",
                green(feature_name),
                idx,
                len(self.features),
            )

            # Query-and-insert in one statement to reduce local memory overhead and remove database round-trips
            while True:
                q_select = self.process_features(
                    feature_name,
                    feature_type=self.features[feature_name]["type"],
                    agg_func=self.features[feature_name]["aggfunc"],
                ).limit(10)

                # import pandas as pd
                print(q_select)
                print("Count number of rows in q_select...")
                print(q_select.count())
                # test = pd.read_sql(q_select.statement, q_select.session.bind)
                # print(test)
                print("=> done")

                if q_select:
                    with self.dbcnxn.open_session() as session:
                        self.commit_records(
                            session,
                            q_select.subquery(),
                            table=self.output_table,
                            on_conflict="ignore",
                        )
                else:
                    break

            # Print a final timing message
            self.logger.info(
                "Finished adding records for %s after %s",
                feature_name,
                green(duration(feature_start, time.time())),
            )
