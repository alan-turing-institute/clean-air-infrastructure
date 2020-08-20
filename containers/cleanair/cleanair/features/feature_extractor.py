"""
Feature extraction Base  class
"""
import time
from datetime import timedelta
from math import ceil
from dateutil.parser import isoparse
from sqlalchemy import func, literal, or_, case, column, String, text
from sqlalchemy.sql.selectable import Alias as SUBQUERY_TYPE
import numpy as np
from ..databases import DBWriter
from ..databases.tables import (
    StaticFeature,
    DynamicFeature,
    UKMap,
    MetaPoint,
    OSHighway,
    ScootRoadMatch,
    ScootReading,
)
from ..mixins.availability_mixins import StaticFeatureAvailabilityMixin
from ..decorators import db_query
from ..mixins import DBQueryMixin, DateRangeMixin
from ..loggers import duration, green, red, get_logger
from ..databases.base import Values
from .feature_conf import FEATURE_CONFIG_DYNAMIC

ONE_HOUR_INTERVAL = text("interval '1 hour'")


class FeatureExtractorMixin:
    @db_query
    def query_meta_points(self, point_ids):
        """
        Query MetaPoints, selecting all matching sources. We do not filter these in
        order to ensure that repeated calls will return the same set of points.
        """

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
            ).filter(MetaPoint.id.in_(point_ids))

        return q_meta_point


class ScootFeatureExtractor(DateRangeMixin, DBWriter, FeatureExtractorMixin):
    def __init__(
        self, features, sources, batch_size=15, insert_method="missing", **kwargs,
    ):
        """Base class for extracting features.
        args:
            dynamic: Boolean. Set whether feature is dynamic (e.g. varies over time)
                     Time must always be named measurement_start_utc
        """
        # Initialise parent classes
        super().__init__(**kwargs)

        self.table_per_detector = ScootReading
        self.output_table = DynamicFeature

        self.features = features
        self.sources = sources if sources else []
        self.feature_map = FEATURE_CONFIG_DYNAMIC["scoot"]["features"]
        if insert_method == "all":
            self.exclude_has_data = False
        else:
            self.exclude_has_data = True
        self.insert_method = insert_method
        self.batch_size = batch_size

    @db_query
    def oshighway_intersection(self, point_ids):

        buffers = self.query_meta_points(point_ids, output_type="subquery")

        with self.dbcnxn.open_session() as session:

            return session.query(
                OSHighway.toid,
                OSHighway.geom,
                buffers.c.id,
                func.ST_Intersects(OSHighway.geom, buffers.c.buff_geom_500).label(
                    "intersects_500"
                ),
                func.ST_Intersects(OSHighway.geom, buffers.c.buff_geom_200).label(
                    "intersects_200"
                ),
                func.ST_Intersects(OSHighway.geom, buffers.c.buff_geom_100).label(
                    "intersects_100"
                ),
                func.ST_Intersects(OSHighway.geom, buffers.c.buff_geom_10).label(
                    "intersects_10"
                ),
            ).filter(func.ST_Intersects(OSHighway.geom, buffers.c.buff_geom_1000))

    @db_query
    def get_scoot_road_match(self, lookup_cte):

        with self.dbcnxn.open_session() as session:
            return (
                session.query(ScootRoadMatch)
                .filter(ScootRoadMatch.road_toid.in_([lookup_cte.c.toid]))
                .order_by(ScootRoadMatch.road_toid)
            )

    @db_query
    def scoot_to_road(self, point_ids, start_datetime, end_datetime):

        intersection_lookup_cte = self.oshighway_intersection(point_ids=point_ids).cte(
            "intersection_lookup"
        )

        scoot_road_match_sq = self.get_scoot_road_match(
            intersection_lookup_cte, output_type="subquery"
        )

        with self.dbcnxn.open_session() as session:

            per_road_forecasts_sq = (
                session.query(
                    scoot_road_match_sq.c.road_toid,
                    self.table_per_detector.measurement_start_utc,
                    (
                        func.sum(
                            self.table_per_detector.n_vehicles_in_interval
                            * scoot_road_match_sq.c.weight
                        )
                        / func.sum(scoot_road_match_sq.c.weight)
                    ).label("n_vehicles_in_interval"),
                    (
                        func.sum(
                            self.table_per_detector.occupancy_percentage
                            * scoot_road_match_sq.c.weight
                        )
                        / func.sum(scoot_road_match_sq.c.weight)
                    ).label("occupancy_percentage"),
                    (
                        func.sum(
                            self.table_per_detector.congestion_percentage
                            * scoot_road_match_sq.c.weight
                        )
                        / func.sum(scoot_road_match_sq.c.weight)
                    ).label("congestion_percentage"),
                    (
                        func.sum(
                            self.table_per_detector.saturation_percentage
                            * scoot_road_match_sq.c.weight
                        )
                        / func.sum(scoot_road_match_sq.c.weight)
                    ).label("saturation_percentage"),
                )
                .join(
                    self.table_per_detector,
                    scoot_road_match_sq.c.detector_n
                    == self.table_per_detector.detector_id,
                )
                .filter(
                    self.table_per_detector.measurement_start_utc >= start_datetime,
                    self.table_per_detector.measurement_start_utc < end_datetime,
                )
                .group_by(
                    self.table_per_detector.measurement_start_utc,
                    scoot_road_match_sq.c.road_toid,
                )
            ).subquery()

            return session.query(intersection_lookup_cte, per_road_forecasts_sq).join(
                intersection_lookup_cte,
                intersection_lookup_cte.c.toid == per_road_forecasts_sq.c.road_toid,
            )

    @db_query
    def get_scoot_features(
        self, point_ids, start_datetime, end_datetime,
    ):

        scoot_road_readings = self.scoot_to_road(
            point_ids, start_datetime, end_datetime
        ).cte()

        with self.dbcnxn.open_session() as session:

            all_queries = []
            for feature in self.features:

                feature_name = feature.value
                column_name = list(
                    self.feature_map[feature.value]["feature_dict"].keys()
                )[0]
                agg_func = self.feature_map[feature.value]["aggfunc"]

                all_queries.append(
                    session.query(
                        scoot_road_readings.c.id,
                        scoot_road_readings.c.measurement_start_utc,
                        literal(feature_name).label("feature_name"),
                        func.coalesce(
                            agg_func(getattr(scoot_road_readings.c, column_name)), 0.0
                        ).label("values_1000"),
                        func.coalesce(
                            agg_func(
                                getattr(scoot_road_readings.c, column_name)
                            ).filter(scoot_road_readings.c.intersects_500),
                            0.0,
                        ).label("values_500"),
                        func.coalesce(
                            agg_func(
                                getattr(scoot_road_readings.c, column_name)
                            ).filter(scoot_road_readings.c.intersects_200),
                            0.0,
                        ).label("values_200"),
                        func.coalesce(
                            agg_func(
                                getattr(scoot_road_readings.c, column_name)
                            ).filter(scoot_road_readings.c.intersects_100),
                            0.0,
                        ).label("values_100"),
                        func.coalesce(
                            agg_func(
                                getattr(scoot_road_readings.c, column_name)
                            ).filter(scoot_road_readings.c.intersects_10),
                            0.0,
                        ).label("values_10"),
                    ).group_by(
                        scoot_road_readings.c.id,
                        scoot_road_readings.c.measurement_start_utc,
                    )
                )

            return all_queries[0].union(*all_queries[1:])

    @db_query
    def get_scoot_feature_availability(
        self, feature_names, sources, start_datetime, end_datetime, exclude_has_data
    ):

        feature_names = [feature.value for feature in feature_names]
        sources = [source.value for source in sources]

        with self.dbcnxn.open_session() as session:

            in_data = (
                session.query(
                    DynamicFeature.point_id,
                    DynamicFeature.measurement_start_utc,
                    DynamicFeature.feature_name,
                )
                .filter(
                    DynamicFeature.feature_name.in_(feature_names),
                    DynamicFeature.measurement_start_utc >= start_datetime,
                    DynamicFeature.measurement_start_utc < end_datetime,
                )
                .subquery()
            )

            # Expected datetimes
            expected_date_times = session.query(
                func.generate_series(
                    start_datetime,
                    (isoparse(end_datetime) - timedelta(hours=1)).isoformat(),
                    ONE_HOUR_INTERVAL,
                ).label("measurement_start_utc")
            ).subquery()

            # Expected ids and feature names
            expected_values = (
                session.query(
                    MetaPoint.id.label("point_id"),
                    MetaPoint.source,
                    Values(
                        [column("feature_name", String),],
                        *[(feature,) for feature in feature_names],
                        alias_name="t2",
                    ),
                )
                .filter(MetaPoint.source.in_(sources))
                .subquery()
            )

            # Expected data
            expected_data = session.query(
                expected_values, expected_date_times
            ).subquery()

            available_data_q = session.query(
                expected_data.c.point_id,
                expected_data.c.measurement_start_utc,
                expected_data.c.feature_name,
                in_data.c.point_id.isnot(None).label("has_data")
                # in_data_cte.c.reference_start_utc.isnot(None).label("has_data"),
                # in_data_cte.c.n_records,
                # (in_data_cte.c.n_records == 72 * 32).label("expected_n_records"),
            ).join(
                in_data,
                (in_data.c.point_id == expected_data.c.point_id)
                & (
                    in_data.c.measurement_start_utc
                    == expected_data.c.measurement_start_utc
                )
                & (in_data.c.feature_name == expected_data.c.feature_name),
                isouter=True,
            )

            if exclude_has_data:
                return available_data_q.filter(in_data.c.point_id.is_(None))
            return available_data_q

    @db_query
    def get_scoot_feature_ids(
        self, feature_names, sources, start_datetime, end_datetime, exclude_has_data
    ):

        available_sq = self.get_scoot_feature_availability(
            feature_names,
            sources,
            start_datetime,
            end_datetime,
            exclude_has_data,
            output_type="subquery",
        )

        with self.dbcnxn.open_session() as session:

            return session.query(
                func.distinct(available_sq.c.point_id).label("point_id")
            )

    @db_query
    def check_remote_table(self):

        # Check which point ids dont have a full dataset
        return self.get_scoot_feature_ids(
            self.features,
            self.sources,
            self.start_datetime.isoformat(),
            self.end_datetime.isoformat(),
            exclude_has_data=self.exclude_has_data,
        )

    def update_remote_tables(self):

        update_start = time.time()

        # Check which point ids dont have a full dataset
        missing_point_ids = self.get_scoot_feature_ids(
            self.features,
            self.sources,
            self.start_datetime.isoformat(),
            self.end_datetime.isoformat(),
            exclude_has_data=self.exclude_has_data,
            output_type="list",
        )

        missing_point_ids = [str(p) for p in missing_point_ids]

        if not missing_point_ids:
            self.logger.info("No interest points require processing")
            return

        n_point_ids = len(missing_point_ids)
        batch_size = self.batch_size
        n_batches = ceil(n_point_ids / min(batch_size, n_point_ids))

        self.logger.info(
            "Processing %s interest points from sources %s in %s batches of max size %s",
            n_point_ids,
            [src.value for src in self.sources],
            n_batches,
            batch_size,
        )

        missing_point_id_batches = np.array_split(missing_point_ids, n_batches)

        for batch_no, point_id_batch in enumerate(missing_point_id_batches, start=1):

            batch_start = time.time()
            self.logger.info("Processing batch %s of %s", batch_no, n_batches)

            sq_select_and_insert = self.get_scoot_features(
                point_ids=point_id_batch.tolist(),
                start_datetime=self.start_datetime.isoformat(),
                end_datetime=self.end_datetime.isoformat(),
                output_type="subquery",
            )

            self.commit_records(
                sq_select_and_insert, on_conflict="ignore", table=self.output_table
            )

            # Print a timing message at the end of each feature
            self.logger.info(
                "Finished adding records after %s",
                green(duration(batch_start, time.time())),
            )

        self.logger.info(
            "Finished adding records after %s",
            green(duration(update_start, time.time())),
        )


class FeatureExtractor(
    DBWriter, FeatureExtractorMixin, StaticFeatureAvailabilityMixin, DBQueryMixin
):
    """Extract features which are near to a given set of MetaPoints and inside London"""

    # pylint: disable=R0913
    def __init__(
        self,
        feature_source,
        table,
        features,
        dynamic=False,
        batch_size=10,
        sources=None,
        insert_method="missing",
        **kwargs,
    ):
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

        self.feature_source = feature_source
        self.table = table
        self.features = features
        self.dynamic = dynamic
        self.sources = sources if sources else []
        self.batch_size = batch_size
        if self.dynamic:
            self.output_table = DynamicFeature
        else:
            self.output_table = StaticFeature

        if insert_method == "all":
            self.exclude_has_data = False
        else:
            self.exclude_has_data = True
        self.insert_method = insert_method

    @property
    def feature_names(self):
        """Return a list of all feature names"""
        return self.features.keys()

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

    # @db_query
    # def get_dynamic_processed(self, feature_name):
    #     """Return the features which have already been processed for a given feature name between
    #     a self.start_datetime and self.end_datetime. To be returned they must have as many hours as would be expected
    #     from the difference between self.start_datetime and self.end_datetime.

    #     args:
    #         feature_name: string
    #             Name of the feature to check for
    #     """

    #     expected_hours = int(
    #         (self.end_datetime - self.start_datetime).total_seconds() / (60 * 60)
    #     )

    #     with self.dbcnxn.open_session() as session:
    #         already_processed_sq = (
    #             session.query(
    #                 DynamicFeature.point_id,
    #                 (
    #                     func.count(DynamicFeature.measurement_start_utc)
    #                     == expected_hours
    #                 ).label("all_hours"),
    #             )
    #             .filter(
    #                 DynamicFeature.feature_name == feature_name,
    #                 DynamicFeature.measurement_start_utc
    #                 >= self.start_datetime.isoformat(),
    #                 DynamicFeature.measurement_start_utc
    #                 < self.end_datetime.isoformat(),
    #             )
    #             .group_by(DynamicFeature.point_id)
    #         ).subquery()

    #         already_processed_q = session.query(already_processed_sq.c.point_id).filter(
    #             already_processed_sq.c.all_hours == True
    #         )

    #         return already_processed_q

    # @db_query
    # def query_features_dynamic(self, feature_name, feature_dict, agg_func, batch_size):
    #     # Get input geometries for this feature
    #     # self.logger.debug(
    #     #     "There are %s input geometries to consider",
    #     #     self.query_input_geometries(feature_name).count(),
    #     # )
    #     # sq_source = self.query_input_geometries(feature_name, output_type="query")

    #     # Get all the metapoints and buffer geometries as a common table expression
    #     cte_buffers = self.query_meta_points(
    #         feature_name=feature_name, exclude_processed=True, limit=batch_size
    #     ).cte("buffers")

    #     n_interest_points = self.query_meta_points(
    #         feature_name=feature_name, exclude_processed=True, output_type="count",
    #     )

    #     if n_interest_points == 0:
    #         self.logger.info(
    #             "There are 0 interest points left to process for feature %s ...",
    #             feature_name,
    #         )
    #         return None

    #     # Output about next batch to be processed
    #     self.logger.info(
    #         "Preparing to analyse %s interest points of %s unprocessed...",
    #         green(batch_size),
    #         green(n_interest_points),
    #     )

    #     with self.dbcnxn.open_session() as session:

    #         # Intersect the buffers with roads
    #         buff_table_intersection_sq = (
    #             session.query(
    #                 cte_buffers.c.id,
    #                 self.table.toid,
    #                 func.ST_Intersects(
    #                     cte_buffers.c.buff_geom_500, self.table.geom
    #                 ).label("Intersects_500"),
    #                 func.ST_Intersects(
    #                     cte_buffers.c.buff_geom_200, self.table.geom
    #                 ).label("Intersects_200"),
    #                 func.ST_Intersects(
    #                     cte_buffers.c.buff_geom_100, self.table.geom
    #                 ).label("Intersects_100"),
    #                 func.ST_Intersects(
    #                     cte_buffers.c.buff_geom_10, self.table.geom
    #                 ).label("Intersects_10"),
    #             )
    #             .filter(
    #                 func.ST_Intersects(cte_buffers.c.buff_geom_1000, self.table.geom)
    #             )
    #             .subquery()
    #         )

    #         # Join the scoot_road_map+data and aggregate over buffers
    #         res = (
    #             session.query(
    #                 buff_table_intersection_sq.c.id,
    #                 self.table_class.measurement_start_utc,
    #                 literal(feature_name).label("feature_name"),
    #                 func.coalesce(
    #                     agg_func(
    #                         getattr(self.table_class, list(feature_dict.keys())[0])
    #                     ),
    #                     0.0,
    #                 ).label("value_1000"),
    #                 func.coalesce(
    #                     agg_func(
    #                         getattr(self.table_class, list(feature_dict.keys())[0])
    #                     ).filter(buff_table_intersection_sq.c.Intersects_500),
    #                     0.0,
    #                 ).label("value_500"),
    #                 func.coalesce(
    #                     agg_func(
    #                         getattr(self.table_class, list(feature_dict.keys())[0])
    #                     ).filter(buff_table_intersection_sq.c.Intersects_200),
    #                     0.0,
    #                 ).label("value_200"),
    #                 func.coalesce(
    #                     agg_func(
    #                         getattr(self.table_class, list(feature_dict.keys())[0])
    #                     ).filter(buff_table_intersection_sq.c.Intersects_100),
    #                     0.0,
    #                 ).label("value_100"),
    #                 func.coalesce(
    #                     agg_func(
    #                         getattr(self.table_class, list(feature_dict.keys())[0])
    #                     ).filter(buff_table_intersection_sq.c.Intersects_10),
    #                     0.0,
    #                 ).label("value_10"),
    #             )
    #             .join(
    #                 self.table_class,
    #                 buff_table_intersection_sq.c.toid == self.table_class.road_toid,
    #             )
    #             .filter(
    #                 self.table_class.measurement_start_utc
    #                 >= self.start_datetime.isoformat(),
    #                 self.table_class.measurement_start_utc
    #                 < self.end_datetime.isoformat(),
    #             )
    #             .group_by(
    #                 buff_table_intersection_sq.c.id,
    #                 self.table_class.measurement_start_utc,
    #             )
    #         )

    #         return res

    @db_query
    def query_features(self, point_ids, feature_name, feature_type, agg_func):
        """
        For a given features, produce a query containing the full feature processing stage.

        This avoids complications when trying to work out which interest points have
        already been processed (easy for static features but very complicated for
        dynamic features).

        As we do not filter interest points as part of the query, it will stay the same
        size on repeated calls and can therefore be sliced for batch operations.
        """
        # # Get input geometries for this feature
        # self.logger.debug(
        #     "There are %s input geometries to consider",
        #     self.query_input_geometries(feature_name).count(),
        # )

        sq_source = self.query_input_geometries(feature_name, output_type="subquery")

        # Get all the metapoints and buffer geometries as a common table expression
        cte_buffers = self.query_meta_points(point_ids=point_ids).cte("buffers")

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
                literal(self.feature_source).label("feature_source"),
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

            missing_point_ids_df = self.get_static_feature_availability(
                [feature_name],
                self.sources,
                exclude_has_data=self.exclude_has_data,
                output_type="df",
            )

            if missing_point_ids_df.empty:
                self.logger.info(
                    "No interest points require processing for feature %s, sources: %s",
                    red(feature_name),
                    red(self.sources),
                )
                continue

            self.logger.info(
                "%s interest points from sources %s require processing for feature %s",
                green(missing_point_ids_df.shape[0]),
                green(self.sources),
                green(feature_name),
            )

            missing_point_ids = missing_point_ids_df["id"].astype(str).values
            n_point_ids = missing_point_ids.size
            batch_size = 250
            n_batches = ceil(n_point_ids / min(batch_size, n_point_ids))

            self.logger.info(
                "Processing %s interest points in %s batches of max size %s",
                missing_point_ids.size,
                n_batches,
                batch_size,
            )

            missing_point_id_batches = np.array_split(missing_point_ids, n_batches)

            for batch_no, point_id_batch in enumerate(missing_point_id_batches):
                self.logger.info("Processing batch %s of %s", batch_no, n_batches)
                sq_select_and_insert = self.query_features(
                    point_id_batch,
                    feature_name,
                    feature_type=self.features[feature_name]["type"],
                    agg_func=self.features[feature_name]["aggfunc"],
                    output_type="subquery",
                )

                self.commit_records(
                    sq_select_and_insert, on_conflict="ignore", table=self.output_table
                )

            # Print a timing message at the end of each feature
            self.logger.info(
                "Finished adding records for '%s' after %s",
                feature_name,
                green(duration(feature_start, time.time())),
            )

        self.logger.info(
            "Finished adding records after %s",
            green(duration(update_start, time.time())),
        )

        # while True:

        #     if self.dynamic:
        #         # Create full select-and-insert query
        #         q_select_and_insert = self.query_features_dynamic(
        #             feature_name,
        #             feature_dict=self.features[feature_name]["feature_dict"],
        #             agg_func=self.features[feature_name]["aggfunc"],
        #             batch_size=self.batch_size,
        #             output_type="query",
        #         )

        #     else:
        #         # Create full select-and-insert query
        #         q_select_and_insert = self.query_features(
        #             feature_name,
        #             feature_type=self.features[feature_name]["type"],
        #             agg_func=self.features[feature_name]["aggfunc"],
        #             batch_size=self.batch_size,
        #             output_type="query",
        #         )

        #     if q_select_and_insert:
        #         self.logger.info("Commiting to database")
        #         with self.dbcnxn.open_session() as session:
        #             self.commit_records(
        #                 q_select_and_insert.subquery(),
        #                 on_conflict="ignore",
        #                 table=self.output_table,
        #             )

        #         quit()
        #     else:
        #         break
