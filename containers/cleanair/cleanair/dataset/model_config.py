"""Vizualise available sensor data for a model fit"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import func, text, cast, String, and_, Any

from cleanair.types.enum_types import DynamicFeatureNames

from cleanair.databases import DBReader
from cleanair.databases.materialised_views import LondonBoundaryView
from cleanair.databases.tables import StaticFeature, DynamicFeature, MetaPoint
from cleanair.decorators import db_query
from cleanair.exceptions import MissingFeatureError, MissingSourceError
from cleanair.loggers import get_logger, green
from cleanair.mixins.availability_mixins import (
    LAQNAvailabilityMixin,
    AQEAvailabilityMixin,
    SatelliteAvailabilityMixin,
)
from cleanair.timestamps import as_datetime
from cleanair.types import (
    Source,
    Species,
    StaticFeatureNames,
    DataConfig,
    FullDataConfig,
    FeatureBufferSize,
    InterestPointDict,
)

ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")


class ModelConfig(
    LAQNAvailabilityMixin, AQEAvailabilityMixin, SatelliteAvailabilityMixin, DBReader
):
    """Create and validate cleanair model configurations
    Runs checks against the database"""

    def __init__(self, **kwargs: Any) -> None:

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
        static_features: List[StaticFeatureNames],
        dynamic_features: List[DynamicFeatureNames],
        buffer_sizes: List[FeatureBufferSize],
        norm_by: str,
    ) -> DataConfig:
        """Return a configuration class"""

        return DataConfig(
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
            static_features=static_features,
            dynamic_features=dynamic_features,
            buffer_sizes=buffer_sizes,
            norm_by=norm_by,
            include_prediction_y=False,
        )

    def validate_config(self, config: DataConfig) -> None:
        """Validate a configuration file

        Check:
            1. requested features are available
            2. requested sources are available for training and prediction periods

        """

        self.logger.info("Validating config")

        self.check_static_features_available(
            config.static_features, config.train_start_date, config.pred_end_date
        )
        self.logger.info(green("Requested static features are available"))

        # TODO if no dynamic features are required then don't validate
        self.check_dynamic_features_available(
            config.dynamic_features, config.train_start_date, config.pred_end_date
        )
        self.logger.info(green("Requested dynamic features are available"))

        # Check training sources are available
        self.check_sources_available(config.train_sources)
        self.logger.info(green("Requested training sources are available"))

        # Check prediction sources are available
        self.check_sources_available(config.pred_sources)
        self.logger.info(green("Requested prediction sources are available"))

        self.logger.info("Validate config complete")

    def generate_full_config(self, config: DataConfig) -> FullDataConfig:
        """Generate a full config file by querying the cleanair
        database to check available interest point sources and features"""

        # Get interest points from database
        config.train_interest_points = self.get_interest_point_ids(
            config.train_interest_points
        )

        config.pred_interest_points = self.get_interest_point_ids(
            config.pred_interest_points
        )

        # Create feature names from features and buffer sizes
        static_feature_names = [
            f"value_{buff.value}_{feature.name}"
            for buff in config.buffer_sizes
            for feature in config.static_features
        ]

        dynamic_feature_names = [
            f"value_{buff.value}_{feature.name}"
            for buff in config.buffer_sizes
            for feature in config.dynamic_features
        ]

        # Add epoch, lat and lon
        x_names = ["epoch", "lat", "lon"] + (
            static_feature_names + dynamic_feature_names
            if dynamic_feature_names
            else static_feature_names
        )

        # Create full config and validate
        config_dict = config.dict()
        config_dict["feature_names"] = (
            static_feature_names + dynamic_feature_names
            if dynamic_feature_names
            else static_feature_names
        )

        config_dict["x_names"] = x_names

        return FullDataConfig(**config_dict)

    def check_static_features_available(
        self,
        features: List[StaticFeatureNames],
        start_date: datetime,
        end_date: datetime,
    ) -> None:
        """Check that all requested static features exist in the database"""

        available_features = self.get_available_static_features(output_type="list")
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

    # pylint: disable=C0103
    def check_dynamic_features_available(
        self,
        features: List[DynamicFeatureNames],
        start_date: datetime,
        end_date: datetime,
    ) -> None:
        """Check that all requested dynamic features exist in the database"""
        if len(features) > 0:
            self.logger.debug("Requested dynamic features: %s", features)
            available_features_list = self.get_available_dynamic_features(
                start_date, end_date, output_type="list"
            )
            available_features = set(available_features_list)
            self.logger.debug("Available dynamic features: %s", available_features)
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

    def check_sources_available(self, sources: List[Source]) -> None:
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

    def get_interest_point_ids(self, interest_point_dict: InterestPointDict) -> Dict:
        """Get ids of interest points"""
        output_dict: InterestPointDict = {}

        for key in interest_point_dict:

            self.logger.info("Getting interest point_ids for %s", key.value)

            if (
                isinstance(interest_point_dict[key], str)
                and interest_point_dict[key] == "all"
            ):
                output_dict[key] = self.get_available_interest_points(
                    key,
                    within_london_only=(key != Source.satellite),
                    output_type="list",
                )

            else:
                output_dict[key] = interest_point_dict[key]

        return output_dict

    @db_query()
    def get_available_static_features(self) -> None:
        """Return available static features from the CleanAir database"""

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(StaticFeature.feature_name).distinct(
                StaticFeature.feature_name
            )

            return feature_types_q

    @db_query()
    def get_available_dynamic_features(
        self, start_datetime: datetime, upto_datetime: datetime
    ) -> None:
        """Return available dynamic features from the CleanAir database

        Notes:
            The list of available features may not be unique
        """

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(DynamicFeature.feature_name).filter(
                and_(
                    DynamicFeature.measurement_start_utc >= start_datetime,
                    DynamicFeature.measurement_start_utc < upto_datetime,
                )
            )

            return feature_types_q

    @db_query()
    def get_available_sources(self) -> None:
        """Return the available interest point sources in a database"""

        with self.dbcnxn.open_session() as session:

            feature_types_q = session.query(MetaPoint.source).distinct(MetaPoint.source)

            return feature_types_q

    @db_query()
    def query_london_boundary(self) -> None:
        """Query LondonBoundary to obtain the bounding geometry for London.
        Only get the first row as should only be one entry"""
        with self.dbcnxn.open_session() as session:

            return session.query(LondonBoundaryView.geom).limit(1)

    @db_query()
    def get_meta_point_ids(self, source: Source) -> None:
        """Get metapoint ids"""
        with self.dbcnxn.open_session() as session:

            return session.query(MetaPoint.id.label("point_id")).filter(
                MetaPoint.source == source
            )

    @db_query()
    def get_available_interest_points(
        self, source: Source, within_london_only: bool
    ) -> None:
        """
        Get available interest points for a particular source
        and optionally filter sites outside of london

        If requesting LAQN or AQE will only return open sites
        If requesting Satellite will only get points from tiles that intersect
            the london boundary. within_london_only will further filter by whether
            interest points themselves are in London.
        """

        bounded_geom = self.query_london_boundary(output_type="subquery")

        if source == Source.laqn:

            point_ids_sq = self.get_laqn_open_sites(output_type="subquery")

        elif source == Source.aqe:

            point_ids_sq = self.get_aqe_open_sites(output_type="subquery")

        elif source == Source.satellite:

            point_ids_sq = self.get_satellite_interest_points_in_boundary(
                output_type="subquery"
            )

        elif source in [Source.hexgrid]:

            point_ids_sq = self.get_meta_point_ids(source, output_type="subquery")

        else:
            raise NotImplementedError("Cannot get interest points for this source")

        with self.dbcnxn.open_session() as session:

            point_ids = session.query(cast(point_ids_sq.c.point_id, String)).join(
                MetaPoint, point_ids_sq.c.point_id == MetaPoint.id
            )

            if within_london_only:
                return point_ids.filter(
                    func.ST_Intersects(MetaPoint.location, bounded_geom.c.geom)
                )

            return point_ids
