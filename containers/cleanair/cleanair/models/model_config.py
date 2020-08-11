"""Vizualise available sensor data for a model fit"""
from __future__ import annotations
from typing import List
from datetime import datetime, timedelta
from sqlalchemy import func, text, and_, cast, String
from ..databases.tables import (
    StaticFeature,
    DynamicFeature,
    MetaPoint,
    HexGrid,
)
from ..databases import DBReader
from ..mixins.availability_mixins import (
    LAQNAvailabilityMixin,
    AQEAvailabilityMixin,
    SatelliteAvailabilityMixin,
)
from ..loggers import get_logger, green
from ..timestamps import as_datetime
from ..decorators import db_query
from ..exceptions import MissingFeatureError, MissingSourceError
from ..types import (
    Source,
    Species,
    FeatureNames,
    BaseConfig,
    FullConfig,
    FeatureBufferSize,
    InterestPointDict,
)


ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")


class ModelConfig(
    LAQNAvailabilityMixin, AQEAvailabilityMixin, SatelliteAvailabilityMixin, DBReader
):
    """Create and validate cleanair model configurations"""

    def __init__(self, **kwargs) -> None:

        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    # pylint: disable=R0913
    @staticmethod
    def generate_data_config(
        trainupto: str,
        trainhours: int,
        predhours: int,
        train_sources: List[Source],
        pred_sources: List[Source],
        species: List[Species],
        features: List[FeatureNames],
        buffer_sizes: List[FeatureBufferSize],
        norm_by: str,
        model_type: str,
    ) -> BaseConfig:
        """Return a configuration class
        """

        return BaseConfig(
            train_start_date=(
                as_datetime(trainupto) - timedelta(hours=trainhours)
            ).isoformat(),
            train_end_date=as_datetime(trainupto).isoformat(),
            pred_start_date=as_datetime(trainupto).isoformat(),
            pred_end_date=(
                as_datetime(trainupto) + timedelta(hours=predhours)
            ).isoformat(),
            train_sources=train_sources,
            pred_sources=pred_sources,
            train_interest_points={src: "all" for src in train_sources},
            pred_interest_points={src: "all" for src in pred_sources},
            species=species,
            features=features,
            buffer_sizes=buffer_sizes,
            norm_by=norm_by,
            model_type=model_type,
            include_prediction_y=False,
        )

    def validate_config(self, config: BaseConfig):
        """Validate a configuration file"""
        self.logger.info("Validating config")

        self.check_features_available(
            config.features, config.train_start_date, config.pred_end_date
        )
        self.logger.info(green("Requested features are available"))

        # Check training sources are available
        self.check_sources_available(config.train_sources)
        self.logger.info(green("Requested training sources are available"))

        # Check prediction sources are available
        self.check_sources_available(config.pred_sources)
        self.logger.info(green("Requested prediction sources are available"))

        # TODO: Validate interest points
        # # Check interest points are valid
        # if isinstance(config.train_interest_points, list):
        #     self.__check_points_available(
        #         config.train_interest_points, config.train_sources
        #     )
        # self.logger.info(green("Requested training interest points are available"))

        # pred_interest_points = config["pred_interest_points"]
        # if isinstance(pred_interest_points, list):
        #     self.__check_points_available(pred_interest_points, pred_sources)
        # self.logger.info(green("Requested prediction interest points are available"))

        # if "satellite" in config["train_sources"]:
        #     satellite_interest_points = config["train_satellite_interest_points"]
        #     if isinstance(satellite_interest_points, list):
        #         self.__check_points_available(pred_interest_points, ["satellite"])
        #     self.logger.info(green("Requested satellite interest points are available"))
        self.logger.info("Validate config complete")

    def generate_full_config(self, config: BaseConfig):
        """Generate a full config file by querying the cleanair
           database to check available interest point sources and features"""

        # Expand interest points
        config.train_interest_points = self.get_interest_point_ids(
            config.train_interest_points
        )
        config.pred_interest_points = self.get_interest_point_ids(
            config.pred_interest_points
        )

        # Create feature names from features and buffer sizes
        feature_names = [
            f"value_{buff.value}_{feature.name}"
            for buff in config.buffer_sizes
            for feature in config.features
        ]

        # Add epoch, lat and lon
        x_names = ["epoch", "lat", "lon"] + feature_names

        # Create full config and validate
        config_dict = config.dict()
        config_dict["feature_names"] = feature_names
        config_dict["x_names"] = x_names

        return FullConfig(**config_dict)

    def check_features_available(
        self, features: List[FeatureNames], start_date: datetime, end_date: datetime
    ) -> None:
        """Check that all requested features exist in the database"""

        available_features = self.get_available_static_features(
            output_type="list"
        ) + self.get_available_dynamic_features(
            start_date, end_date, output_type="list"
        )
        unavailable_features = []

        for feature in features:
            if feature.value not in available_features:
                unavailable_features.append(feature)
        if unavailable_features:
            raise MissingFeatureError(
                """The following features are not available the cleanair database: {}.
                   If requesting dynamic features they may not be available for the selected dates""".format(
                    unavailable_features
                )
            )

    def check_sources_available(self, sources: List[Source]):
        """Check that sources are available in the database

        args:
            sources: A list of sources
        """

        available_sources = self.get_available_sources(output_type="list")
        unavailable_sources = []

        for source in sources:
            if source.value not in available_sources:
                unavailable_sources.append(source)

        if unavailable_sources:
            raise MissingSourceError(
                "The following sources are not available the cleanair database: {}".format(
                    unavailable_sources
                )
            )

    def get_interest_point_ids(self, interest_point_dict: InterestPointDict):
        """Get ids of interest points"""
        output_dict: InterestPointDict = {}

        for key in interest_point_dict:

            if (
                isinstance(interest_point_dict[key], str)
                and interest_point_dict[key] == "all"
            ):
                output_dict[key] = self.get_available_interest_points(
                    key, output_type="list"
                )

            else:
                output_dict[key] = interest_point_dict[key]

        return output_dict

    @db_query
    def get_available_static_features(self):
        """Return available static features from the CleanAir database
        """

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(StaticFeature.feature_name).distinct(
                StaticFeature.feature_name
            )

            return feature_types_q

    @db_query
    def get_available_dynamic_features(self, start_date, end_date):
        """Return a list of the available dynamic features in the database.
            Only returns features that are available between start_date and end_date
        """

        with self.dbcnxn.open_session() as session:

            available_dynamic_sq = (
                session.query(
                    DynamicFeature.feature_name,
                    func.min(DynamicFeature.measurement_start_utc).label("min_date"),
                    func.max(DynamicFeature.measurement_start_utc).label("max_date"),
                )
                .group_by(DynamicFeature.feature_name)
                .subquery()
            )

            available_dynamic_q = session.query(available_dynamic_sq).filter(
                and_(
                    available_dynamic_sq.c["min_date"] <= start_date,
                    available_dynamic_sq.c["max_date"] >= end_date,
                )
            )

            return available_dynamic_q

    @db_query
    def get_available_sources(self):
        """Return the available interest point sources in a database"""

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(MetaPoint.source).distinct(MetaPoint.source)

            return feature_types_q

    @db_query
    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London"""
        with self.dbcnxn.open_session() as session:

            hull = session.query(
                func.ST_MakePolygon(
                    func.ST_Boundary((func.ST_Dump(func.ST_Union(HexGrid.geom))).geom)
                ).label("geom")
            )

        return hull

    @db_query
    def get_meta_point_ids(self, source: Source):
        """Get metapoint ids"""
        with self.dbcnxn.open_session() as session:

            return session.query(MetaPoint.id.label("point_id")).filter(
                MetaPoint.source == source
            )

    @db_query
    def get_available_interest_points(self, source: Source):
        """
        Get available interest points for a particular source
        """

        # bounded_geom = self.query_london_boundary(output_type="subquery")

        # To Do: Filter by bounding geometry. Geometry should be a materialiized view

        if source == Source.laqn:

            point_ids_sq = self.get_laqn_open_sites(output_type="subquery")

        elif source == Source.aqe:

            point_ids_sq = self.get_aqe_open_sites(output_type="subquery")

        elif source in [Source.satellite, Source.hexgrid]:

            point_ids_sq = self.get_meta_point_ids(source, output_type="subquery")

        else:
            raise NotImplementedError("Cannot get interest points for this source")

        with self.dbcnxn.open_session() as session:

            # Ensure we always return a string
            return session.query(cast(point_ids_sq.c.point_id, String))
