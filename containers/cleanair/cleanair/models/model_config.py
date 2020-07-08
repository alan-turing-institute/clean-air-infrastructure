"""Vizualise available sensor data for a model fit"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Union, Optional, Tuple
from datetime import date, datetime, timedelta
import json
import os
import pickle
import pandas as pd
import numpy as np
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
from sqlalchemy import func, text, and_, null
from sqlalchemy.sql.expression import Alias
from patsy import dmatrices, dmatrix
from ..databases.tables import (
    StaticFeature,
    DynamicFeature,
    AirQualityDataTable,
    SatelliteGrid,
    MetaPoint,
    LondonBoundary,
    AQESite,
    LAQNSite,
)

from ..databases import DBWriter, Base
from ..mixins import DBQueryMixin
from ..loggers import get_logger, green, red
from ..utils import hash_dict
from ..timestamps import as_datetime
from ..decorators import db_query

# if TYPE_CHECKING:
from ..types import (
    DataConfig,
    Source,
    Species,
    FeatureNames,
    BaseConfig,
    FullConfig,
    FeatureBufferSize,
)


ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")


class ModelConfig(DBWriter):
    """Create and validate cleanair model configurations"""

    def __init__(self, **kwargs) -> None:

        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

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
            train_sources=[src.value for src in train_sources],
            pred_sources=[src.value for src in pred_sources],
            train_interest_points="all",
            train_satellite_interest_points="all",
            pred_interest_points="all",
            species=[src.value for src in species],
            features=[ftr for ftr in features],
            buffer_sizes=[buff for buff in buffer_sizes],
            norm_by=norm_by,
            model_type=model_type,
            include_prediction_y=False,
        )

    def validate_config(self, config: BaseConfig):

        self.logger.info("Validating config")

        self.logger.debug("Checking requested features are available in database")
        self.__check_features_available(
            config.features, config.train_start_date, config.pred_end_date
        )
        self.logger.info(green("Requested features are available"))

        # Check training sources are available
        self.logger.debug(
            "Checking requested sources for training are available in database"
        )
        self.__check_sources_available(config.train_sources)
        self.logger.info(green("Requested training sources are available"))

        # Check prediction sources are available
        self.logger.debug(
            "Checking requested sources for prediction are available in database"
        )
        self.__check_sources_available(config.pred_sources)
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

    def generate_full_config(self, config):
        """Generate a full config file by querying the cleanair
           database to check available interest point sources and features"""

        if config.train_interest_points == "all":
            config.train_interest_points = self.__get_interest_point_ids(
                config.train_sources
            )
        if config.pred_interest_points == "all":
            config.pred_interest_points = self.__get_interest_point_ids(
                config.pred_sources
            )

        print(config.train_interest_points)
        quit()
        # if config["include_satellite"] and (
        #     config["train_satellite_interest_points"] == "all"
        # ):
        #     config["train_satellite_interest_points"] = self.__get_interest_point_ids(
        #         ["satellite"]
        #     )
        # else:
        #     config["train_satellite_interest_points"] = []

        if config["features"] == "all":
            feature_names = self.get_available_static_features(
                output_type="list"
            ) + self.get_available_dynamic_features(
                config["train_start_date"], config["pred_end_date"], output_type="list"
            )
            buff_size = [1000, 500, 200, 100, 10]
            config["features"] = [
                "value_{}_{}".format(buff, name)
                for buff in buff_size
                for name in feature_names
            ]
            self.logger.info(
                "Features 'all' replaced with available features: %s",
                config["features"],
            )
            config["feature_names"] = feature_names
        else:
            config["feature_names"] = list(
                {"".join(feature.split("_", 2)[2:]) for feature in config["features"]}
            )

        config["x_names"] = ["epoch", "lat", "lon"] + config["features"]

        return FullConfig(**config)

    def __check_features_available(
        self, features: List[FeatureNames], start_date: datetime, end_date: datetime
    ):
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
            raise AttributeError(
                """The following features are not available the cleanair database: {}.
                   If requesting dynamic features they may not be available for the selected dates""".format(
                    unavailable_features
                )
            )

    def __check_sources_available(self, sources: List[Source]):
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
            raise AttributeError(
                "The following sources are not available the cleanair database: {}".format(
                    unavailable_sources
                )
            )

    def __get_interest_point_ids(self, sources):

        return (
            self.get_available_interest_points(sources, output_type="df")["point_id"]
            .astype(str)
            .to_numpy()
            .tolist()
        )

    def __check_points_available(
        self, interest_points: List[str], sources: List[Source]
    ):

        available_interest_points = self.__get_interest_point_ids(sources)
        unavailable_interest_points = []

        for point in interest_points:
            if point not in available_interest_points:
                unavailable_interest_points.append(point)

        if unavailable_interest_points:
            raise AttributeError(
                "The following interest points are not available the cleanair database: {}".format(
                    unavailable_interest_points
                )
            )

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

    def query_london_boundary(self):
        """Query LondonBoundary to obtain the bounding geometry for London"""
        with self.dbcnxn.open_session() as session:
            hull = session.scalar(
                func.ST_ConvexHull(func.ST_Collect(LondonBoundary.geom))
            )
        return hull

    @db_query
    def get_available_interest_points(self, sources, point_ids=None):
        """Return the available interest points for a list of sources, excluding any LAQN or AQE sites that are closed.
        Only returns points withing the London boundary
        Satellite returns features outside of london boundary, while laqn and aqe do not.
        args:
            sources: A list of sources to include
            point_ids: A list of point_ids to include. Default of None returns all points
        """

        bounded_geom = self.query_london_boundary()
        base_query_columns = [
            MetaPoint.id.label("point_id"),
            MetaPoint.source.label("source"),
            MetaPoint.location.label("location"),
            MetaPoint.location.ST_Within(bounded_geom).label("in_london"),
            func.ST_X(MetaPoint.location).label("lon"),
            func.ST_Y(MetaPoint.location).label("lat"),
        ]

        with self.dbcnxn.open_session() as session:

            remaining_sources_q = session.query(
                *base_query_columns,
                null().label("date_opened"),
                null().label("date_closed"),
            ).filter(
                MetaPoint.source.in_(
                    [
                        source
                        for source in sources
                        if source not in ["laqn", "aqe", "satellite"]
                    ]
                ),
                MetaPoint.location.ST_Within(bounded_geom),
            )

            # Satellite is not filtered by london boundary
            sat_sources_q = session.query(
                *base_query_columns,
                null().label("date_opened"),
                null().label("date_closed"),
            ).filter(MetaPoint.source.in_(["satellite"]))

            aqe_sources_q = (
                session.query(
                    *base_query_columns,
                    func.min(AQESite.date_opened),
                    func.min(AQESite.date_closed),
                )
                .join(AQESite, isouter=True)
                .group_by(*base_query_columns)
                .filter(
                    MetaPoint.source.in_(["aqe"]),
                    MetaPoint.location.ST_Within(bounded_geom),
                )
            )

            laqn_sources_q = (
                session.query(
                    *base_query_columns,
                    func.min(LAQNSite.date_opened),
                    func.min(LAQNSite.date_closed),
                )
                .join(LAQNSite, isouter=True)
                .group_by(*base_query_columns)
                .filter(
                    MetaPoint.source.in_(["laqn"]),
                    MetaPoint.location.ST_Within(bounded_geom),
                )
            )

            # if ("satellite" in sources) and (len(sources) != 1):
            #     raise ValueError(
            #         """Satellite can only be requested on a source on its own.
            #         Ensure 'sources' contains no other options"""
            #     )
            if sources[0] == "satellite":
                all_sources_sq = remaining_sources_q.union(sat_sources_q).subquery()
            else:
                all_sources_sq = remaining_sources_q.union(
                    aqe_sources_q, laqn_sources_q
                ).subquery()

            # Remove any sources where there is a closing date and filter by point_ids
            all_sources_q = session.query(all_sources_sq).filter(
                all_sources_sq.c.date_closed.is_(None)
            )

            if point_ids:
                all_sources_q = all_sources_q.filter(
                    all_sources_sq.c.point_id.in_(point_ids)
                )

        return all_sources_q
