"""
Feature extraction Base  class
"""
import time
from sqlalchemy import func, literal, tuple_, or_, case
from sqlalchemy.sql.selectable import Alias as SUBQUERY_TYPE
from ..databases import DBWriter
from ..databases.tables import (
    IntersectionValue,
    IntersectionValueDynamic,
    InterestPointBuffers,
    UKMap,
)
from ..decorators import db_query
from ..mixins import DBQueryMixin
from ..loggers import duration, green, red, get_logger


class Features(DBWriter, DBQueryMixin):
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

    @db_query
    def query_meta_points(
        self, include_sources=None, exclude_processed=True, feature_name=None
    ):
        """Query MetaPoints, selecting all matching include_sources"""

        with self.dbcnxn.open_session() as session:

            meta_point_q = session.query(InterestPointBuffers)

            if exclude_processed:
                already_processed_sq = (
                    session.query(
                        IntersectionValue.point_id, IntersectionValue.feature_name
                    )
                    .filter(IntersectionValue.feature_name == feature_name)
                    .subquery()
                )

                meta_point_q = meta_point_q.filter(
                    ~tuple_(InterestPointBuffers.id, literal(feature_name)).in_(
                        already_processed_sq
                    )
                )

            if include_sources:
                meta_point_q = meta_point_q.filter(
                    InterestPointBuffers.source.in_(include_sources)
                )

        return meta_point_q

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

    def process_features(self, feature_name, feature_type, agg_func, batch_size=1):
        """
        Process geometric features in large batches as none of them are particularly slow at present
        (and they need to be independentely calculated for each interest point anyway)
        """

        # Get geometries for this feature
        sq_source = self.query_features(feature_name, output_type="subquery")

        # Get all the metapoints and buffer geometries as a common table expression
        cte_buffers = self.query_meta_points(
            include_sources=self.sources, feature_name=feature_name, limit=batch_size
        ).cte("buffers")

        n_interest_points = self.query_meta_points(
            include_sources=self.sources, feature_name=feature_name, output_type="count"
        )

        if n_interest_points == 0:
            self.logger.info(
                "There are 0 interest points left to process for feature %s ...",
                red(feature_name),
            )
            return None

        self.logger.info(
            "Preparing to analyse %s interest points of %s unprocessed...",
            red(batch_size),
            green(n_interest_points),
        )

        if feature_type == "geom":
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

            res = (
                session.query(
                    cte_buffers.c.id,
                    value_1000.label("value_1000"),
                    value_500.label("value_500"),
                    value_200.label("value_200"),
                    value_100.label("value_100"),
                    value_10.label("value_10"),
                )
                .join(
                    sq_source,
                    func.ST_Intersects(sq_source.c.geom, cte_buffers.c.buff_1000),
                )
                .group_by(cte_buffers.c.id)
                .subquery()
            )

            # Left join with coalesce to make sure we always return a value
            out = session.query(
                cte_buffers.c.id,
                literal(feature_name).label("feature_name"),
                func.coalesce(res.c.value_1000, 0.0).label("value_1000"),
                func.coalesce(res.c.value_500, 0.0).label("value_500"),
                func.coalesce(res.c.value_200, 0.0).label("value_200"),
                func.coalesce(res.c.value_100, 0.0).label("value_100"),
                func.coalesce(res.c.value_10, 0.0).label("value_10"),
            ).join(res, cte_buffers.c.id == res.c.id, isouter=True)

            return out

    def calculate_intersections(self):
        """
        For each interest point location, for each feature:
        extract the geometry for that feature in each of the buffer radii
        """
        # Iterate over each of the features and calculate the overlap with the interest points
        for feature_name in self.features:
            feature_start = time.time()
            self.logger.info("Now working on the %s feature", green(feature_name))

            # Query-and-insert in one statement to reduce local memory overhead and remove database round-trips
            while True:
                select_stmt = self.process_features(
                    feature_name,
                    feature_type=self.features[feature_name]["type"],
                    agg_func=self.features[feature_name]["aggfunc"],
                    batch_size=10,
                )

                if select_stmt:

                    self.logger.debug("%s", select_stmt.statement.compile(compile_kwargs={"literal_binds": True}))

                    with self.dbcnxn.open_session() as session:
                        self.commit_records(
                            session,
                            select_stmt.subquery(),
                            table=IntersectionValue,
                            on_conflict_do_nothing=True,
                        )
                else:
                    break

            # Print a final timing message
            self.logger.info(
                "Finished adding records after %s",
                green(duration(feature_start, time.time())),
            )

    def update_remote_tables(self):
        """Update all remote tables"""
        self.calculate_intersections()
