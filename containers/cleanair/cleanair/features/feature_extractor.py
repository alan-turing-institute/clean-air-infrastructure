"""
Feature extraction Base  class
"""
import time
from datetime import timedelta
from math import ceil
from typing import List

import numpy as np
from dateutil.parser import isoparse
from sqlalchemy import func, literal, or_, and_, case, column, String, text, Float
from sqlalchemy.sql.selectable import Alias as SUBQUERY_TYPE

from .feature_conf import FEATURE_CONFIG_DYNAMIC
from ..databases import DBWriter
from ..databases.base import Values
from ..databases.tables import (
    StaticFeature,
    DynamicFeature,
    UKMap,
    MetaPoint,
    ScootForecast,
    ScootReading,
    ScootDetector,
)
from ..decorators import db_query
from ..loggers import duration, green, red, get_logger
from ..mixins import DBQueryMixin, DateRangeMixin
from ..mixins.availability_mixins import StaticFeatureAvailabilityMixin
from ..types.enum_types import Source

ONE_HOUR_INTERVAL = text("interval '1 hour'")


class FeatureExtractorMixin:
    "Mixin for feature extractors"

    @db_query()
    def query_meta_points(self, point_ids: List[str]):
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
    "Scoot feature extractor"

    def __init__(
        self,
        features,
        sources,
        batch_size=15,
        n_workers=1,
        forecast=True,
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

        self.n_workers = n_workers
        self.forecast = forecast

        self.table_per_detector = ScootReading
        if self.forecast:
            self.table_per_detector = ScootForecast

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

    @db_query()
    def latest_forecast(self, start_datetime: str, end_datetime: str):
        "Get the latest scoot forecast that covers start_datetime and end_datetime"

        with self.dbcnxn.open_session() as session:
            forecast_cte = (
                session.query(self.table_per_detector)
                .filter(
                    self.table_per_detector.measurement_start_utc >= start_datetime,
                    self.table_per_detector.measurement_start_utc < end_datetime,
                )
                .order_by(
                    self.table_per_detector.detector_id,
                    self.table_per_detector.measurement_start_utc,
                )
                .cte("raw_forecast")
            )

            latest_forecast = (
                session.query(
                    forecast_cte.c.measurement_start_utc,
                    func.max(forecast_cte.c.forecasted_on).label("max_forecast"),
                )
                .group_by(forecast_cte.c.measurement_start_utc)
                .subquery("all_data")
            )

            return session.query(forecast_cte).join(
                latest_forecast,
                and_(
                    latest_forecast.c.measurement_start_utc
                    == forecast_cte.c.measurement_start_utc,
                    latest_forecast.c.max_forecast == forecast_cte.c.forecasted_on,
                ),
            )

    @db_query()
    def generate_scoot_features(
        self,
        point_ids: List[str],
        start_datetime: str,
        end_datetime: str,
        n_detectors: int,
    ):
        """Generated scoot features for a set of points (no buffer used)"""

        self.logger.info("Currently populating all value columns with a fixed value")

        with self.dbcnxn.open_session() as session:
            all_queries = []
            for feature in self.features:
                feature_name = feature.value
                agg_func = self.feature_map[feature.value]["aggfunc"]

                points = (
                    session.query(
                        MetaPoint.id.label("point_id"),
                        MetaPoint.location.label("point_location"),
                    )
                    .filter(MetaPoint.id.in_(point_ids))
                    .subquery()
                    .lateral()
                )

                nearest_detectors = (
                    session.query(
                        MetaPoint.id.label("detector_id"),
                        MetaPoint.location.label("detector_location"),
                    )
                    .filter(MetaPoint.source == "scoot")
                    .order_by(
                        func.ST_Distance(points.c.point_location, MetaPoint.location)
                    )
                    .limit(n_detectors)
                    .subquery()
                    .lateral()
                )

                maps = session.query(
                    points.join(nearest_detectors, literal(True))
                ).subquery()

                distances = session.query(
                    maps.c.point_id.label("point_id"),
                    maps.c.detector_id.label("detector_id"),
                    func.ST_Distance(
                        func.Geography(maps.c.point_location),
                        func.Geography(maps.c.detector_location),
                    ).label("distance"),
                ).subquery()

                readings = (
                    session.query(
                        distances.c.point_id.label("point_id"),
                        ScootForecast.measurement_start_utc.label(
                            "measurement_start_utc"
                        ),
                        literal(feature_name).label("feature_name"),
                        func.coalesce(
                            agg_func(ScootForecast.n_vehicles_in_interval), 0.0
                        )
                        .label("value_1000")
                        .cast(Float),
                        func.coalesce(
                            agg_func(ScootForecast.n_vehicles_in_interval), 0.0
                        )
                        .label("value_500")
                        .cast(Float),
                        func.coalesce(
                            agg_func(ScootForecast.n_vehicles_in_interval), 0.0
                        )
                        .label("value_200")
                        .cast(Float),
                        func.coalesce(
                            agg_func(ScootForecast.n_vehicles_in_interval), 0.0
                        )
                        .label("value_100")
                        .cast(Float),
                        func.coalesce(
                            agg_func(ScootForecast.n_vehicles_in_interval), 0.0
                        )
                        .label("value_10")
                        .cast(Float),
                    )
                    .join(
                        ScootDetector, ScootDetector.point_id == distances.c.detector_id
                    )
                    .join(
                        ScootForecast,
                        ScootForecast.detector_id == ScootDetector.detector_n,
                    )
                    .filter(ScootForecast.measurement_start_utc >= start_datetime)
                    .filter(ScootForecast.measurement_start_utc < end_datetime)
                    .group_by(distances.c.point_id, ScootForecast.measurement_start_utc)
                )

                all_queries.append(readings)

            return all_queries[0].union(*all_queries[1:])

    @db_query()
    def get_scoot_feature_availability(
        self,
        feature_names,
        sources: List[Source],
        start_datetime: str,
        end_datetime: str,
        exclude_has_data: bool,
    ):
        "Check which scoot features have been processed"
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
                        [
                            column("feature_name", String),
                        ],
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
                in_data.c.point_id.isnot(None).label("has_data"),
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

    @db_query()
    def get_scoot_feature_ids(
        self,
        feature_names,
        sources: List[Source],
        start_datetime: str,
        end_datetime: str,
        exclude_has_data: bool,
    ):
        "Get Ids of interest points and whether they have been processed between start_datetime and end_datetime"
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

    @db_query()
    def check_remote_table(self):
        "Check what scoot features have been processed"
        # Check which point ids dont have a full dataset
        return self.get_scoot_feature_ids(
            self.features,
            self.sources,
            self.start_datetime.isoformat(),
            self.end_datetime.isoformat(),
            exclude_has_data=self.exclude_has_data,
        )

    def update_remote_tables(self):
        "Run scoot feature processing and write to database"

        update_start = time.time()

        n_detectors = 5
        while n_detectors <= 50:

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
                break

            self.logger.info(
                "Generating features for %s points..", len(missing_point_ids)
            )

            sq_select_and_insert = self.generate_scoot_features(
                point_ids=missing_point_ids,
                start_datetime=self.start_datetime.isoformat(),
                end_datetime=self.end_datetime.isoformat(),
                output_type="subquery",
                n_detectors=n_detectors,
            )

            self.commit_records(
                sq_select_and_insert, on_conflict="overwrite", table=self.output_table
            )

            n_detectors += 5
        # pylint: disable=logging-fstring-interpolation
        self.logger.info(f"Done in {time.time() - update_start:.2f}s")


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

    @db_query()
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
            for column_, values in self.features[feature_name]["feature_dict"].items():
                if (len(values) >= 1) and (values[0] != "*"):
                    filter_list.append(
                        or_(*[getattr(table, column_) == value for value in values])
                    )
            q_source = q_source.filter(*filter_list)
        return q_source

    @db_query()
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
                    sq_select_and_insert,
                    on_conflict="overwrite",
                    table=self.output_table,
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
