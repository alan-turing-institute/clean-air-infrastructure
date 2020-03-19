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

    def __init__(self, dynamic=False, batch_size=10, sources=None, **kwargs):
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

            if exclude_processed and (not self.dynamic):

                preprocessed = self.get_static_processed(feature_name=feature_name).cte(
                    "processed"
                )

                q_meta_point = q_meta_point.filter(
                    ~tuple_(MetaPoint.id, literal(feature_name)).in_(preprocessed)
                )

        return q_meta_point

    @db_query
    def query_features_dynamic(
        self, feature_name, feature_type, feature_dict, agg_func, batch_size
    ):
        """IMPLIMENT THIS:

        WITH buffers AS 
(SELECT interest_points.meta_point.id AS id, interest_points.meta_point.source AS source, Geometry(ST_Buffer(Geography(interest_points.meta_point.location), 1000)) AS buff_geom_1000, Geometry(ST_Buffer(Geography(interest_points.meta_point.location), 500)) AS buff_geom_500, Geometry(ST_Buffer(Geography(interest_points.meta_point.location), 200)) AS buff_geom_200, Geometry(ST_Buffer(Geography(interest_points.meta_point.location), 100)) AS buff_geom_100, Geometry(ST_Buffer(Geography(interest_points.meta_point.location), 10)) AS buff_geom_10 
FROM interest_points.meta_point 
WHERE ST_Within(interest_points.meta_point.location, '0103000020E610000001000000400000003E374B70ACD1BFBF548CE781B4A449405FE8C7DCF9F6D4BFB87D01CCC4A9494020BD38FEB702D5BF37FCD385C9A9494057248DFE9E17D5BF4E37C603E1A94940DD0C6B6D9D20D5BFD965E115ECA949406AB767B73054E0BFA4507736D7BB4940F8BCB83FBE54E0BFFE2AB9E2E5BB4940134B563ED654E0BFCE7A734FEABB4940DCE438528402E0BF246B568680D049403DAF01913302E0BF747635E582D04940A8F5A0E519F8DFBF1F165F98AAD04940D3C98ED615F7DFBFD286C856ADD04940219C8639BCF5DFBFF9904440B0D04940A0A6F4B6E7F3DFBF1F353790B3D04940777931F08CF1DFBF889B1319B7D0494064BA95AE84E8DFBF8007A8EAC1D049405FCEF4E112D9DFBF4510ABB3D3D0494066B3EAA475D5DFBF5D7F3C87D7D049400B40BA4F8DD2DFBF0B2A9E22DAD049406D2F6CB3C8CEDFBF28C285CEDBD04940C859B3E15AEDC4BF3C50572714D84940E4878E264AF8BBBF5C8A191E8BD849400C4B00B1BCAFBBBF7221DF898DD849406AE527ACC284BBBF94223EEE8ED849406F524E471652BBBF093D64608FD849408594B5C78C28BBBF5000AD6C8FD84940F4FBF5275B14BBBF45D322618FD8494093E5C6D6CE04BBBF660BA5578FD84940F84B16785BD7BABF7FF31D908ED84940C3D3312EAB93BABFABAADC198CD849408D09CB6713DBB5BF192668AE56D8494062BD8C68D3B6B5BF7ADDD4C354D849401D0328FF9AA986BF94AC5CBC26D74940C5E08523E7AECC3F581F04C8DCD049400814F32B4C17D03F7A5F6AF51FCF494074527735E01AD03F705484501CCF4940000668BCF223D03F7E15101113CF4940E52444B4C92CD03FEE512E0809CF4940B071F713C72DD03F053D52E707CF4940D01A7128F435D03F6B6BDBD5FDCE4940BC461EA3A042D03F60827E1CEDCE4940DBE592AA057ED03F430A0A889DCE4940460A0F0115E7D03FF21865AFEFCD49400B2B5FA1C308D43FA3D994BA6CC849405A60423FEFFAD43FB3F752FD86C649403A7D2E408FFBD43F7FDBDB8C85C64940FBACCC290551D53F869B90CB9BC549403E6303FBA75ED53F2961206F70C549407793ABC8F960D53FCA19908C34C54940CAAA868BA660D53FCDD3653A2FC5494060823F26DF57B73FD7223070FEA5494048EC89462052B73F5D23F53FFCA549409DB0C7D23603B63FAC3615B689A549407028464FF8EFB53F44814DC883A549406438B66E74E9B53F6BB5086D82A5494063BB296FCED4B53FE024A3A17EA54940441DCE180852B53F00DCDAA168A5494015890EEE6DE2B43FED7354DC5AA549407205F1BCEADEB43F8CAFB47A5AA549406D1B5756C998B43FC5837D3D56A5494032C91195E26EB03F380D34FB1AA549409357E18B4208AE3F7B9854D709A5494055676F2708F5AD3F2F34E58A09A549403E374B70ACD1BFBF548CE781B4A44940') AND interest_points.meta_point.source IN ('aqe', 'laqn', 'satellite', 'grid_100') AND (interest_points.meta_point.id, 'max_n_vehicles') NOT IN (SELECT model_features.static_feature.point_id, model_features.static_feature.feature_name 
FROM model_features.static_feature 
WHERE model_features.static_feature.feature_name = 'max_n_vehicles')
 LIMIT 100)
select id, processed_data.scoot_road_reading2.measurement_start_utc, max(processed_data.scoot_road_reading2.n_vehicles_in_interval) filter (where Intersect_1000) 
from (SELECT buffers.id, static_data.oshighway_roadlink.toid, buffers.source, ST_Intersects(buffers.buff_geom_1000, static_data.oshighway_roadlink.geom) as Intersect_1000, ST_Intersects(buffers.buff_geom_500, static_data.oshighway_roadlink.geom) as Intersect_500, ST_Intersects(buffers.buff_geom_200, static_data.oshighway_roadlink.geom) as Intersect_200, ST_Intersects(buffers.buff_geom_100, static_data.oshighway_roadlink.geom) as Intersect_100, ST_Intersects(buffers.buff_geom_10, static_data.oshighway_roadlink.geom) as Intersect_10
FROM buffers, static_data.oshighway_roadlink
where ST_Intersects(buffers.buff_geom_1000, static_data.oshighway_roadlink.geom)) A
left join  processed_data.scoot_road_reading2 on  A.toid = processed_data.scoot_road_reading2.road_toid 
group by (id, processed_data.scoot_road_reading2.measurement_start_utc)
"""
        # Get input geometries for this feature
        # self.logger.debug(
        #     "There are %s input geometries to consider",
        #     self.query_input_geometries(feature_name).count(),
        # )
        # sq_source = self.query_input_geometries(feature_name, output_type="query")

        # Get all the metapoints and buffer geometries as a common table expression
        cte_buffers = self.query_meta_points(
            feature_name=feature_name, exclude_processed=True, limit=batch_size
        ).cte("buffers")

        with self.dbcnxn.open_session() as session:

            buff_table_intersection_sq = (
                session.query(
                    cte_buffers.c.id,
                    self.table.toid,
                    cte_buffers.c.source,
                    func.ST_Intersects(
                        cte_buffers.c.buff_geom_1000, self.table.geom
                    ).label("Intersects_1000"),
                    func.ST_Intersects(
                        cte_buffers.c.buff_geom_500, self.table.geom
                    ).label("Intersects_500"),
                    func.ST_Intersects(
                        cte_buffers.c.buff_geom_200, self.table.geom
                    ).label("Intersects_200"),
                    func.ST_Intersects(
                        cte_buffers.c.buff_geom_100, self.table.geom
                    ).label("Intersects_100"),
                    func.ST_Intersects(
                        cte_buffers.c.buff_geom_10, self.table.geom
                    ).label("Intersects_10"),
                )
                .filter(
                    func.ST_Intersects(cte_buffers.c.buff_geom_1000, self.table.geom)
                )
                .subquery()
            )

            res = (
                session.query(
                    buff_table_intersection_sq.c.id,
                    self.table_class.measurement_start_utc,
                    literal(feature_name).label("feature_name"),
                    func.coalesce(
                        agg_func(
                            getattr(self.table_class, list(feature_dict.keys())[0])
                        ).filter(buff_table_intersection_sq.c.Intersects_1000),
                        0.0,
                    ).label("value_1000"),
                    func.coalesce(
                        agg_func(
                            getattr(self.table_class, list(feature_dict.keys())[0])
                        ).filter(buff_table_intersection_sq.c.Intersects_500),
                        0.0,
                    ).label("value_500"),
                    func.coalesce(
                        agg_func(
                            getattr(self.table_class, list(feature_dict.keys())[0])
                        ).filter(buff_table_intersection_sq.c.Intersects_200),
                        0.0,
                    ).label("value_200"),
                    func.coalesce(
                        agg_func(
                            getattr(self.table_class, list(feature_dict.keys())[0])
                        ).filter(buff_table_intersection_sq.c.Intersects_100),
                        0.0,
                    ).label("value_100"),
                    func.coalesce(
                        agg_func(
                            getattr(self.table_class, list(feature_dict.keys())[0])
                        ).filter(buff_table_intersection_sq.c.Intersects_10),
                        0.0,
                    ).label("value_10"),
                )
                .join(
                    self.table_class,
                    buff_table_intersection_sq.c.toid == self.table_class.road_toid,
                )
                .group_by(
                    buff_table_intersection_sq.c.id,
                    self.table_class.measurement_start_utc,
                )
            )

            return res

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
        self.logger.debug(
            "There are %s input geometries to consider",
            self.query_input_geometries(feature_name).count(),
        )
        sq_source = self.query_input_geometries(feature_name, output_type="query")

        # Get all the metapoints and buffer geometries as a common table expression
        cte_buffers = self.query_meta_points(
            feature_name=feature_name, exclude_processed=True, limit=batch_size
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

                if self.dynamic:
                    # Create full select-and-insert query
                    q_select_and_insert = self.query_features_dynamic(
                        feature_name,
                        feature_type=self.features[feature_name]["type"],
                        feature_dict=self.features[feature_name]["feature_dict"],
                        agg_func=self.features[feature_name]["aggfunc"],
                        batch_size=self.batch_size,
                        output_type="query",
                    )

                else:
                    # Create full select-and-insert query
                    q_select_and_insert = self.query_features(
                        feature_name,
                        feature_type=self.features[feature_name]["type"],
                        agg_func=self.features[feature_name]["aggfunc"],
                        batch_size=self.batch_size,
                        output_type="query",
                    )

                if q_select_and_insert:
                    self.logger.info("Commiting to database")
                    with self.dbcnxn.open_session() as session:
                        self.commit_records(
                            session,
                            q_select_and_insert.subquery(),
                            on_conflict="ignore",
                            table=self.output_table,
                        )
                else:
                    break

                quit()

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
