"""Vizualise available sensor data for a model fit"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict, List, Union, Optional, Tuple, overload
from datetime import date, datetime, timedelta
import json
import os
import pickle
import pandas as pd
import numpy as np
from nptyping import NDArray, Float64
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
from sqlalchemy import func, text, and_, null, column, String
from sqlalchemy.sql.expression import Alias
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
from ..databases.base import Values
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
    BaseConfig,
    FullConfig,
    FeatureNames,
    FeaturesDict,
    IndexDict,
    IndexedDatasetDict,
    TargetDict,
)

# pylint: disable=too-many-lines

ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")


def get_val(x):
    if len(x) == 1:
        return x
    raise ValueError(
        """Pandas pivot table trying to return an array of values.
                        Here it must only return a single value"""
    )


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
        norm_by: str,
        model_type: str,
    ) -> BaseConfig:
        """Return a dictionary of model data settings.

        Args:
            trainupto: Get training data upto (but not including) this datetime.
                ISO datetime string.

        Keyword Args:
            hexgrid: If true add hexgrid to the list of prediction sources.
            include_satellite: If true modeldata will train on satellite data.
            predhours: Number of hours in the prediction period.
            trainhours: Number of hours to train the model for.

        Returns:
            A dictionary of data settings generated from the arguments.
        """

        # Generate and return the config dictionary
        data_config = {
            "train_start_date": (
                as_datetime(trainupto) - timedelta(hours=trainhours)
            ).isoformat(),
            "train_end_date": as_datetime(trainupto).isoformat(),
            "pred_start_date": as_datetime(trainupto).isoformat(),
            "pred_end_date": (
                as_datetime(trainupto) + timedelta(hours=predhours)
            ).isoformat(),
            "train_sources": [src.value for src in train_sources],
            "pred_sources": [src.value for src in pred_sources],
            "train_interest_points": "all",
            "train_satellite_interest_points": "all",
            "pred_interest_points": "all",
            "species": [src.value for src in species],
            "features": [
                "value_1000_total_a_road_length",
                "value_500_total_a_road_length",
                "value_500_total_a_road_primary_length",
                "value_500_total_b_road_length",
            ],
            "norm_by": norm_by,
            "model_type": model_type,
            "include_prediction_y": False,
        }

        return BaseConfig(**data_config)

    def validate_config(self, config):

        config_keys = [
            "train_start_date",
            "train_end_date",
            "pred_start_date",
            "pred_end_date",
            "include_prediction_y",
            "train_sources",
            "pred_sources",
            "train_interest_points",
            "train_satellite_interest_points",
            "pred_interest_points",
            "species",
            "features",
            "norm_by",
            "model_type",
        ]

        valid_models = ["svgp"]

        self.logger.info("Validating config")

        # Check required config keys present
        if not set(config_keys).issubset(set(config.keys())):
            raise AttributeError(
                "Config dictionary does not contain correct keys. Must contain {}".format(
                    config_keys
                )
            )
        self.logger.info(green("Config has correct keys and is syntactically valid"))

        # Check requested features are available
        if config["features"] == "all":
            features = self.get_available_static_features(
                output_type="list"
            ) + self.get_available_dynamic_features(
                config["train_start_date"], config["pred_end_date"], output_type="list"
            )
            if not features:
                raise AttributeError(
                    "There are no features in the database. Run feature extraction first"
                )
            self.logger.warning(
                """You have selected 'all' features from the database.
                It is strongly advised that you choose features manually"""
            )
            self.logger.warning(red("Using all features. Not recommended"))
        else:
            self.logger.debug("Checking requested features are available in database")
            self.__check_features_available(
                config["features"], config["train_start_date"], config["pred_end_date"]
            )
            self.logger.info(green("Requested features are available"))

        # Check training sources are available
        train_sources = config["train_sources"]
        self.logger.debug(
            "Checking requested sources for training are available in database"
        )
        self.__check_sources_available(train_sources)
        self.logger.info(green("Requested training sources are available"))

        # Check prediction sources are available
        pred_sources = config["pred_sources"]
        self.logger.debug(
            "Checking requested sources for prediction are availble in database"
        )
        self.__check_sources_available(pred_sources)
        self.logger.info(green("Requested prediction sources are available"))

        # Check model type is valid
        if config["model_type"] not in valid_models:
            raise AttributeError(
                "{} is not a valid model type. Use one of the following: {}".format(
                    config["model_type"], valid_models
                )
            )
        self.logger.info(green("Model type is valid"))

        # Check interest points are valid
        train_interest_points = config["train_interest_points"]
        if isinstance(train_interest_points, list):
            self.__check_points_available(train_interest_points, train_sources)
        self.logger.info(green("Requested training interest points are available"))

        pred_interest_points = config["pred_interest_points"]
        if isinstance(pred_interest_points, list):
            self.__check_points_available(pred_interest_points, pred_sources)
        self.logger.info(green("Requested prediction interest points are available"))

        if "satellite" in config["train_sources"]:
            satellite_interest_points = config["train_satellite_interest_points"]
            if isinstance(satellite_interest_points, list):
                self.__check_points_available(pred_interest_points, ["satellite"])
            self.logger.info(green("Requested satellite interest points are available"))
        self.logger.info("Validate config complete")

    def generate_full_config(self, config):
        """Generate a full config file by querying the cleanair
           database to check available interest point sources and features"""

        if config["train_interest_points"] == "all":
            config["train_interest_points"] = self.__get_interest_point_ids(
                config["train_sources"]
            )
        if config["pred_interest_points"] == "all":
            config["pred_interest_points"] = self.__get_interest_point_ids(
                config["pred_sources"]
            )
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

    def __check_features_available(self, features, start_date, end_date):
        """Check that all requested features exist in the database"""

        available_features = self.get_available_static_features(
            output_type="list"
        ) + self.get_available_dynamic_features(
            start_date, end_date, output_type="list"
        )
        unavailable_features = []

        for feature in features:
            feature_name_no_buff = "_".join(feature.split("_")[2:])
            if feature_name_no_buff not in available_features:
                unavailable_features.append(feature)

        if unavailable_features:
            raise AttributeError(
                """The following features are not available the cleanair database: {}.
                   If requesting dynamic features they may not be available for the selected dates""".format(
                    unavailable_features
                )
            )

    def __check_sources_available(self, sources):
        """Check that sources are available in the database

        args:
            sources: A list of sources
        """

        available_sources = self.get_available_sources(output_type="list")
        unavailable_sources = []

        for source in sources:
            if source not in available_sources:
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

    def __check_points_available(self, interest_points, sources):

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


class ModelData(DBWriter, DBQueryMixin):
    """Read data from multiple database tables in order to get data for model fitting"""

    def __init__(self, **kwargs):
        """
        Initialise the ModelData object with a config file
        args:
            config: A config dictionary
            config_dir: A directory containing config files
                        (created by ModelData.save_config_state())
        """

        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

        self.feature_index_names = [
            "point_id",
            "measurement_start_utc",
            "lat",
            "lon",
        ]
        self.sensor_index_names = self.feature_index_names + [
            "species_code",
            "value",
        ]
        self.sensor_satellite_index_names = self.sensor_index_names + ["box_id"]

        self.column_names = [
            "feature_name",
            "value_1000",
            "value_500",
            "value_200",
            "value_100",
            "value_10",
        ]
        self.preprocessing: Dict = dict()

    @staticmethod
    def flatten_column_names(data_frame: pd.DataFrame) -> pd.DataFrame:
        "Flaten column names of 2D column names"

        new_column_names = [
            "_".join(col).strip() if (len(col[1]) > 0) else col[0]
            for col in data_frame.columns.to_numpy()
        ]

        data_frame.columns = new_column_names

        return data_frame

    def download_source_data(
        self,
        with_sensor_readings: bool,
        start_date: datetime,
        end_date: datetime,
        species: List[Species],
        point_ids: List[str],
        features: List[FeatureNames],
        source: Source,
    ) -> pd.DataFrame:
        """Download all training data (static, dynamic[not yet implimented] and sensor readings)
        for a given source (e.g. laqn, aqe, satellite)
        """

        if with_sensor_readings:
            # Get source dataframe
            source_data = self.get_training_data_inputs(
                start_date=start_date,
                end_date=end_date,
                species=species,
                point_ids=point_ids,
                features=features,
                source=source,
                output_type="df",
            )
            if source == Source.satellite:
                index_names = self.sensor_satellite_index_names
            else:
                index_names = self.sensor_index_names

        else:
            # Get source dataframe
            source_data = self.get_prediction_data_inputs(
                start_date=start_date,
                end_date=end_date,
                point_ids=point_ids,
                features=features,
                source=source,
                output_type="df",
            )
            index_names = self.feature_index_names

        source_data_index = source_data.set_index(index_names)

        if not set(source_data_index.columns) == set(self.column_names):
            raise AttributeError("Wrong column names")
        if not set(source_data_index.index.names) == set(index_names):
            raise AttributeError("Wrong index names")

        features_df = pd.pivot_table(
            source_data, index=index_names, columns="feature_name", aggfunc=get_val,
        ).reset_index()
        flattend_features_df = self.flatten_column_names(features_df)
        flattend_features_df["epoch"] = flattend_features_df[
            "measurement_start_utc"
        ].apply(lambda x: x.timestamp())

        # If sensor readings then make species a columns
        if with_sensor_readings:

            index_cols = [
                col
                for col in flattend_features_df.columns
                if col not in ("species_code", "value")
            ]

            return pd.pivot_table(
                flattend_features_df,
                index=index_cols,
                columns="species_code",
                values="value",
                aggfunc=get_val,
            ).reset_index()

        return flattend_features_df

    def download_training_config_data(
        self, full_config: FullConfig
    ) -> Dict[Source, pd.DateFrame]:
        """Download all input data specified in a validated full config file"""

        data_output: Dict[Source, pd.DateFrame] = {}
        for source in full_config.train_sources:
            data_output[source] = self.download_source_data(
                with_sensor_readings=True,
                start_date=full_config.train_start_date,
                end_date=full_config.train_end_date,
                species=full_config.species,
                point_ids=full_config.train_interest_points[source],
                features=full_config.features,
                source=source,
            )
        return data_output

    def download_prediction_config_data(
        self, full_config: FullConfig
    ) -> Dict[Source, pd.DataFrame]:

        data_output: Dict[Source, pd.DateFrame] = {}
        for source in full_config.pred_sources:
            data_output[source] = self.download_source_data(
                with_sensor_readings=False,
                start_date=full_config.pred_start_date,
                end_date=full_config.pred_end_date,
                species=full_config.species,
                point_ids=full_config.pred_interest_points[source],
                features=full_config.features,
                source=source,
            )
        return data_output

    @overload
    def get_array(
        self, data_df: pd.DataFrame, x_names, species: None
    ) -> Tuple[pd.Index, NDArray[Float64]]:
        ...

    @overload
    def get_array(
        self, data_df: pd.DataFrame, x_names, species: List[Species]
    ) -> Tuple[pd.Index, NDArray[Float64], Dict[Species, NDArray[Float64]]]:
        ...

    def get_array(self, data_df, x_names, species=None):
        """Get an array from a pandas dataframe for any Source except satellite"""
        index = data_df.index.to_numpy()
        X = data_df[x_names].to_numpy()

        if species:
            Y: Dict[Species, NDArray[Float64]] = {
                spec: np.expand_dims(data_df[spec.value].to_numpy(), axis=1)
                for spec in species
            }

            return index, X, Y

        return index, X

    def get_array_satellite(
        self, data_df: pd.DataFrame, x_names, species: List[Species]
    ) -> Tuple[pd.Index, NDArray[Float64], Dict[Species, NDArray[Float64]]]:
        """Always returns an index, X and Y"""

        data_df_sorted = data_df.sort_values(
            ["box_id", "measurement_start_utc", "point_id"]
        )
        # Save the index
        index = data_df_sorted.index.to_numpy()

        # Get dimensions
        n_boxes = data_df_sorted["box_id"].unique().size
        n_hours = data_df_sorted["epoch"].unique().size
        n_x_names = len(x_names)
        interest_point_counts_all = (
            data_df_sorted.groupby("box_id")
            .apply(lambda x: x["point_id"].unique().size)
            .to_numpy()
        )
        n_interest_points = interest_point_counts_all[0]

        if not np.all(n_interest_points == interest_point_counts_all):
            raise ValueError(
                "All satelllite boxes did not have an equal number of interest points"
            )

        # Get X_array
        sat_df = data_df_sorted[x_names]
        X = sat_df.to_numpy().reshape((n_boxes * n_hours, n_interest_points, n_x_names))
        Y: Dict[Species, NDArray[Float64]] = {}

        # Get Y_array
        for spec in species:
            sat_y = (
                data_df_sorted[spec.value]
                .to_numpy()
                .reshape((n_boxes * n_hours, n_interest_points))
            )
            if not np.all(sat_y.T[0] == sat_y.T[:]):
                raise ValueError(
                    "Satellite points within each box do not have matching values"
                )
            Y[spec] = np.expand_dims(sat_y[:, 0], axis=1)

        return index, X, Y

    def get_data_arrays(
        self,
        full_config: FullConfig,
        data_frame_dict: Dict[Source, pd.DataFrame],
        prediction: bool = False,
    ) -> IndexedDatasetDict:

        species = full_config.species
        x_names = self.x_names_norm(full_config.x_names)
        X_dict: FeaturesDict = {}
        Y_dict: TargetDict = {source: {} for source in data_frame_dict.keys()}
        index_dict: FeaturesDict = {source: {} for source in data_frame_dict.keys()}

        for source in data_frame_dict.keys():

            data_df = data_frame_dict[source]
            if source != Source.satellite:
                if prediction:
                    index_dict[source], X_dict[source] = self.get_array(
                        data_df, x_names
                    )
                else:
                    # Save the index
                    index_dict[source], X_dict[source], Y_dict[source] = self.get_array(
                        data_df, x_names, species
                    )

            else:
                (
                    index_dict[source],
                    X_dict[source],
                    Y_dict[source],
                ) = self.get_array_satellite(data_df, x_names, species)

        return X_dict, Y_dict, index_dict

    def norm_stats(
        self, full_config: FullConfig, data_frames: Dict[str, pd.DateFrame]
    ) -> Tuple[pd.Series, pd.Series]:
        """Normalise a dataset"""

        norm_mean: pd.Series = data_frames[full_config.norm_by.value][
            full_config.x_names
        ].mean(axis=0)

        norm_std: pd.Series = data_frames[full_config.norm_by.value][
            full_config.x_names
        ].std(axis=0)

        if norm_std.eq(0).any().any():
            self.logger.warning(
                "No variance in feature: %s. Setting variance to 1.",
                norm_std[norm_std == 0].index,
            )
            norm_std[norm_std == 0] = 1

        return norm_mean, norm_std

    def normalize_data(
        self, full_config: FullConfig, data_frames: Dict[str, pd.DateFrame]
    ) -> Dict[str, pd.DateFrame]:
        """Normalise the x columns"""

        norm_mean, norm_std = self.norm_stats(full_config, data_frames)

        x_names_norm = self.x_names_norm(full_config.x_names)

        data_output: Dict[str, pd.DateFrame] = {}
        for source, data_df in data_frames.items():

            data_df_normed = data_df.copy()

            data_df_normed[x_names_norm] = (
                data_df_normed[full_config.x_names] - norm_mean
            ) / norm_std

            data_output[source] = data_df_normed

        return data_output

    @property
    def data_id(self) -> str:
        """Hash of the data config dictionary."""
        data_config = ModelData.make_config_json_serializable(self.config)
        return hash_dict(data_config)

    @staticmethod
    def make_config_json_serializable(data_config: DataConfig):
        """Converts any date or datetime values to a string formatted to ISO.

        Args:
            data_config: Contains some values with datetimes or dates.

        Returns:
            New data config with date/datetime values changed to ISO strings.
            Note the returned data config is a NEW object, i.e. we copy the `data_config` parameter.
        """
        new_config = data_config.copy()
        for key, value in data_config.items():
            if isinstance(value, (date, datetime)):
                new_config[key] = value.isoformat()
        return new_config

    @staticmethod
    def config_to_datetime(data_config: DataConfig) -> DataConfig:
        """The values of keys that have 'data' or 'time' in the name
        are converted to a datetime object from a string.

        Args:
            data_config: Config settings for a model data object.

        Returns:
            New data config dictionary with same keys and datetime values where appropriate.
        """
        for key, value in data_config.items():
            if "date" in key or "time" in key:
                data_config[key] = as_datetime(value)
        return data_config

        # return data_config

    def save_config_state(self, dir_path):
        """Save the full configuration and training/prediction data to disk:

        args:
            dir_path: Directory path in which to save the config files
        """

        # Create a new directory
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)

        # Write the files to the directory
        self.normalised_training_data_df.to_csv(
            os.path.join(dir_path, "normalised_training_data.csv")
        )
        self.normalised_pred_data_df.to_csv(
            os.path.join(dir_path, "normalised_pred_data.csv")
        )

        if self.config["include_satellite"]:

            self.training_satellite_data_x.to_csv(
                os.path.join(dir_path, "normalised_satellite_data_x.csv")
            )
            self.training_satellite_data_y.to_csv(
                os.path.join(dir_path, "normalised_satellite_data_y.csv")
            )

        with open(os.path.join(dir_path, "config.json"), "w") as config_f:
            json.dump(self.config, config_f, sort_keys=True, indent=4)

        self.logger.info("State files saved to %s", dir_path)

    def restore_config_state(self, dir_path):
        "Reload configuration state saved to disk by ModelData.save_config_state()"
        if not os.path.exists(dir_path):
            raise IOError("{} does not exist".format(dir_path))

        with open(os.path.join(dir_path, "config.json"), "r") as config_f:
            self.config = json.load(config_f)

        self.normalised_training_data_df = pd.read_csv(
            os.path.join(os.path.join(dir_path, "normalised_training_data.csv")),
            index_col=0,
        )
        self.normalised_pred_data_df = pd.read_csv(
            os.path.join(os.path.join(dir_path, "normalised_pred_data.csv")),
            index_col=0,
        )

        if self.config["include_satellite"]:
            self.training_satellite_data_x = pd.read_csv(
                os.path.join(os.path.join(dir_path, "normalised_satellite_data_x.csv")),
                index_col=0,
            )
            self.training_satellite_data_y = pd.read_csv(
                os.path.join(os.path.join(dir_path, "normalised_satellite_data_y.csv")),
                index_col=0,
            )

        if (
            self.config["tag"] == "validation"
        ):  # TODO replace with flag for loading data
            # load train and test dicts from pickle
            with open(os.path.join(dir_path, "train.pickle"), "rb") as handle:
                self.training_dict = pickle.load(handle)
            with open(os.path.join(dir_path, "test.pickle"), "rb") as handle:
                self.test_dict = pickle.load(handle)

    def x_names_norm(self, x_names):
        """Get the normalised x names"""
        return [x + "_norm" for x in x_names]

    # @property
    # def norm_stats(self):
    #     """Get the mean and sd used for data normalisation"""

    #     norm_mean = self.training_data_df[
    #         self.training_data_df["source"] == self.config["norm_by"]
    #     ][self.config["x_names"]].mean(axis=0)

    #     norm_std = self.training_data_df[
    #         self.training_data_df["source"] == self.config["norm_by"]
    #     ][self.config["x_names"]].std(axis=0)

    #     # Check for zero variance and set to 1 if found
    #     if norm_std.eq(0).any().any():
    #         self.logger.warning(
    #             "No variance in feature: %s. Setting variance to 1.",
    #             norm_std[norm_std == 0].index,
    #         )
    #         norm_std[norm_std == 0] = 1

    #     return norm_mean, norm_std

    def __normalise_data(self, data_df):
        """Normalise the x columns"""
        norm_mean, norm_std = self.norm_stats

        # Normalise the data
        data_df[self.x_names_norm] = (
            data_df[self.config["x_names"]] - norm_mean
        ) / norm_std
        return data_df

    def __get_model_data_arrays(self, data_df, sources, species, **kwargs):
        """Return a dictionary structure of data arrays for model fitting.

        Parameters
        ___

        data_df : DataFrame
            All of the data in one dataframe.

        sources : list
            A list of interest point sources, e.g. 'laqn', 'satellite'.

        species : list
            Pollutants to get data for, e.g. 'NO2', 'o3'.

        Returns
        ___

        data_dict : dict
            A dictionary structure will all the requested data inside.
            See examples for details.

        Other Parameters
        ___

        return_y : bool, optional
            Default is True.
            If true, the returned dictionary will have a 'Y' key/value.

        dropna : bool, optional
            Default is False.
            If true, any rows in data_df that contain NaN will be dropped.

        return_sat : bool, optional
            Default is True.
            Returns satellite if "include_satellite" flag is also True in config.

        Notes
        ___

        The returned dictionary includes index to allow model predictions
        to be appended to dataframes (required when dropna is used).
        At the moment, `laqn_NO2_index` and `laqn_pm10_index` will be the same.
        But in the future if we want to drop some rows for specific pollutants
        then these indices may be different.
        """
        # get key word arguments
        return_y = True if "return_y" not in kwargs else kwargs["return_y"]
        dropna = False if "dropna" not in kwargs else kwargs["dropna"]
        return_sat = True if "return_sat" not in kwargs else kwargs["return_sat"]

        data_dict = dict(X=dict(), index=dict(),)
        if return_y:
            data_dict["Y"] = dict()
            data_subset = data_df[self.x_names_norm + self.config["species"]]
        else:
            data_subset = data_df[self.x_names_norm]
        if dropna:
            data_subset = data_subset.dropna()  # Must have complete dataset
            n_dropped_rows = data_df.shape[0] - data_subset.shape[0]
            self.logger.warning(
                "Dropped %s rows out of %s from the dataframe",
                n_dropped_rows,
                data_df.shape[0],
            )
        # iterate through sources
        for src in sources:
            if src == "satellite":
                raise NotImplementedError(
                    "Satellite cannot be a source - see issue 212 on GitHub."
                )
            # case for laqn, aqe, grid
            src_mask = data_df[data_df["source"] == src].index
            x_src = data_subset.loc[src_mask.intersection(data_subset.index)]
            data_dict["X"][src] = x_src[self.x_names_norm].to_numpy()
            if return_y:
                # get a numpy array for the pollutant of shape (n,1)
                data_dict["Y"][src] = {
                    pollutant: np.reshape(x_src[pollutant].to_numpy(), (len(x_src), 1))
                    for pollutant in species
                }
            # store index
            data_dict["index"][src] = {
                pollutant: x_src.index.copy() for pollutant in species
            }
        # special case for satellite data
        if self.config["include_satellite"] and return_sat:
            if len(species) > 1:
                raise NotImplementedError("Can only get satellite data for NO2")
            # Check dimensions
            n_sat_box = self.training_satellite_data_x["box_id"].unique().size
            n_hours = self.training_satellite_data_x["epoch"].unique().size
            # Number of interest points in each satellite square
            n_interest_points = 100
            n_x_names = len(self.config["x_names"])
            X_sat = (
                self.training_satellite_data_x[self.x_names_norm]
                .to_numpy()
                .reshape((n_sat_box * n_hours, n_interest_points, n_x_names))
            )
            X_sat_mask = (
                self.training_satellite_data_x["in_london"]
                .to_numpy()
                .reshape(n_sat_box * n_hours, n_interest_points)
            )
            Y_sat = self.training_satellite_data_y["value"].to_numpy()
            Y_sat = np.reshape(Y_sat, (Y_sat.shape[0], 1))
            data_dict["X"]["satellite"] = X_sat
            if return_y:
                data_dict["Y"]["satellite"] = dict(NO2=Y_sat)
            data_dict["mask"] = dict(satellite=X_sat_mask)
        return data_dict

    def get_training_data_arrays(
        self, sources="all", species="all", return_y=True, dropna=False
    ):
        """The training data arrays.

        Notes
        ___
        If the `include_satellite` flag is set to `True` in `config`,
        then satellite is always returned as a source.
        """
        # get all sources and species as default
        if sources == "all":
            sources = self.config["train_sources"]
        if species == "all":
            species = self.config["species"]
        # get the data dictionaries
        return self.__get_model_data_arrays(
            self.normalised_training_data_df,
            sources,
            species,
            return_y=return_y,
            dropna=dropna,
        )

    def get_pred_data_arrays(
        self, sources="all", species="all", return_y=False, dropna=False
    ):
        """The pred data arrays.

        args:
            return_y: Return the sensor data if in the database for the prediction dates
            dropna: Drop any rows which contain NaN

        Notes
        ___

        Satellite is never included as a key, value for prediction arrays
        because it is considered a training source only.
        """
        # get all sources and species as default
        if sources == "all":
            sources = self.config["pred_sources"]
        if species == "all":
            species = self.config["species"]
        # return the y column as well
        if self.config["include_prediction_y"] or return_y:
            return self.__get_model_data_arrays(
                self.normalised_pred_data_df,
                sources,
                species,
                return_y=True,
                dropna=dropna,
                return_sat=False,
            )
        # return dicts without y
        return self.__get_model_data_arrays(
            self.normalised_pred_data_df,
            sources,
            species,
            return_y=False,
            dropna=dropna,
            return_sat=False,
        )

    def __select_features(
        self,
        feature_table: Base,
        features: List[str],
        sources: List[Source],
        point_ids: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ):  # pylint: disable=too-many-arguments
        """Query features from the database. Returns a pandas dataframe if values returned, else returns None"""

        # print(features)
        # print(sources)
        # print(point_ids)
        # print(start_date)
        # print(end_date)
        # quit()

        with self.dbcnxn.open_session() as session:

            feature_query = session.query(feature_table).filter(
                feature_table.feature_name.in_(features)
            )

            if start_date and end_date:
                feature_query = feature_query.filter(
                    feature_table.measurement_start_utc >= start_date,
                    feature_table.measurement_start_utc < end_date,
                )

            interest_point_query = self.get_available_interest_points(
                sources, point_ids
            )

            # Select into into dataframes
            features_df = pd.read_sql(
                feature_query.statement, feature_query.session.bind
            )

            print(features_df.head())

            interest_point_df = pd.read_sql(
                interest_point_query.statement, interest_point_query.session.bind
            ).set_index("point_id")

            print(interest_point_df.head())

            # Check if returned dataframes are empty
            if interest_point_df.empty:
                raise AttributeError(
                    "No interest points were returned from the database. Check requested interest points are valid"
                )

            if features_df.empty:
                return features_df

            def get_val(x):
                if len(x) == 1:
                    return x
                raise ValueError(
                    """Pandas pivot table trying to return an array of values.
                                    Here it must only return a single value"""
                )

            # Reshape features df (make wide)
            if start_date:
                features_df = pd.pivot_table(
                    features_df,
                    index=["point_id", "measurement_start_utc"],
                    columns="feature_name",
                    aggfunc=get_val,
                ).reset_index()
                features_df.columns = ["point_id", "measurement_start_utc"] + [
                    "_".join(col).strip() for col in features_df.columns.to_numpy()[2:]
                ]
                features_df = features_df.set_index("point_id")
            else:
                features_df = features_df.pivot(
                    index="point_id", columns="feature_name"
                ).reset_index()
                features_df.columns = ["point_id"] + [
                    "_".join(col).strip() for col in features_df.columns.to_numpy()[1:]
                ]
                features_df = features_df.set_index("point_id")

            # Set index types to str
            features_df.index = features_df.index.astype(str)
            interest_point_df.index = interest_point_df.index.astype(str)

            # Inner join the MetaPoint and StaticFeature(Dynamic) data
            df_joined = interest_point_df.join(features_df, how="left")

            print(df_joined.head())
            quit()
            return df_joined.reset_index()

    @db_query
    def select_static_features(
        self, features: List[FeatureNames], source: Source, point_ids: List[str]
    ):

        with self.dbcnxn.open_session() as session:

            return (
                session.query(
                    StaticFeature,
                    MetaPoint.source,
                    func.ST_X(MetaPoint.location).label("lon"),
                    func.ST_Y(MetaPoint.location).label("lat"),
                )
                .filter(
                    StaticFeature.feature_name.in_(features),
                    MetaPoint.source == source,
                )
                .join(MetaPoint, MetaPoint.id == StaticFeature.point_id)
            )

    def __select_dynamic_features(
        self, start_date, end_date, features, sources, point_ids
    ):
        """Read static features from the database."""

        return self.__select_features(
            DynamicFeature, features, sources, point_ids, start_date, end_date
        )

    def __select_static_features(
        self, features: List[str], sources: List[Source], point_ids: List[str]
    ):
        """Query the database for static features and join with metapoint data

        args:
            source: A list of sources(e.g. 'laqn', 'aqe') to include. Default will include all sources
            point_ids: A list if interest point ids. Default to all ids"""

        return self.__select_features(StaticFeature, features, sources, point_ids)

    @staticmethod
    def __expand_time(start_date, end_date, feature_df):
        """
        Returns a new dataframe with static features merged with
        hourly timestamps between start_date(inclusive) and end_date
        """
        start_date = start_date.date()
        end_date = end_date.date()

        ids = feature_df["point_id"].to_numpy()
        times = rrule.rrule(
            rrule.HOURLY, dtstart=start_date, until=end_date - relativedelta(hours=+1)
        )
        index = pd.MultiIndex.from_product(
            [ids, pd.to_datetime(list(times), utc=False)],
            names=["point_id", "measurement_start_utc"],
        )
        time_df = pd.DataFrame(index=index).reset_index()

        time_df_merged = time_df.merge(feature_df)

        time_df_merged["epoch"] = time_df_merged["measurement_start_utc"].apply(
            lambda x: x.timestamp()
        )
        return time_df_merged

    @db_query
    def get_sensor_readings(
        self,
        start_date: datetime,
        end_date: datetime,
        sources: List[Source],
        species: List[Species],
    ):
        """Get sensor readings for the sources between the start_date(inclusive) and end_date"""

        self.logger.debug(
            "Getting sensor readings for sources: %s, species: %s, from %s (inclusive) to %s (exclusive)",
            sources,
            species,
            start_date,
            end_date,
        )

        sensor_dfs = []
        if "laqn" in sources:
            laqn_sensor_data = self.get_laqn_readings(
                start_date, end_date, output_type="df"
            )
            sensor_dfs.append(laqn_sensor_data)
            if laqn_sensor_data.shape[0] == 0:
                raise AttributeError(
                    "No laqn sensor data was retrieved from the database. Check data exists for the requested dates"
                )

        if "aqe" in sources:
            aqe_sensor_data = self.get_aqe_readings(
                start_date, end_date, output_type="df"
            )
            sensor_dfs.append(aqe_sensor_data)
            if aqe_sensor_data.shape[0] == 0:
                raise AttributeError(
                    "No laqn sensor data was retrieved from the database. Check data exists for the requested dates"
                )

        sensor_df = pd.concat(sensor_dfs, axis=0)

        sensor_df["point_id"] = sensor_df["point_id"].astype(str)
        sensor_df["epoch"] = sensor_df["measurement_start_utc"].apply(
            lambda x: x.timestamp()
        )
        sensor_df = sensor_df.pivot_table(
            index=["point_id", "source", "measurement_start_utc", "epoch"],
            columns=["species_code"],
            values="value",
        )

        return sensor_df[species].reset_index()

    @db_query
    def expand_time_species(
        self,
        subquery: Alias,
        start_date: datetime,
        end_date: datetime,
        species: Optional[List[Species]] = None,
    ):

        with self.dbcnxn.open_session() as session:

            cols = [
                func.generate_series(
                    start_date.isoformat(),
                    (end_date - timedelta(hours=1)).isoformat(),
                    ONE_HOUR_INTERVAL,
                ).label("measurement_start_utc"),
                subquery,
            ]

            if species:

                cols.append(
                    Values(
                        [column("species_code", String),],
                        *[(polutant.value,) for polutant in species],
                        alias_name="t2",
                    )
                )

            return session.query(*cols)

    def get_static_features(
        self,
        start_date: datetime,
        end_date: datetime,
        features: List[FeatureNames],
        source: Source,
        point_ids: List[str],
        species: Optional[List[Species]] = None,
        output_type="df",
    ) -> pd.DateFrame:
        """
        Query the database for static features
        """

        static_features = self.select_static_features(
            features, source, point_ids, output_type="subquery"
        )

        static_features_expand = self.expand_time_species(
            static_features, start_date, end_date, species, output_type=output_type
        )

        return static_features_expand

        # print(static_features_expand)
        # quit()
        # dynamic_features = self.__select_dynamic_features(
        #     start_date, end_date, features, sources, point_ids
        # )

        # if dynamic_features.empty:
        #     self.logger.warning(
        #         """No dynamic features were returned from the database.
        #         If dynamic features were not requested then ignore."""
        #     )
        #     return static_features_expand

        # return static_features_expand.merge(
        #     dynamic_features,
        #     how="left",
        #     on=["point_id", "measurement_start_utc", "source", "lon", "lat"],
        # )

    @db_query
    def join_features_to_sensors(
        self, static_features: Alias, sensor_readings: Alias, source: Source,
    ):

        columns = [
            static_features.c.point_id,
            static_features.c.measurement_start_utc,
            static_features.c.feature_name,
            static_features.c.value_1000,
            static_features.c.value_500,
            static_features.c.value_200,
            static_features.c.value_100,
            static_features.c.value_10,
            static_features.c.lat,
            static_features.c.lon,
            sensor_readings.c.species_code,
            sensor_readings.c.value,
        ]

        if source == Source.satellite:
            columns.append(sensor_readings.c.box_id)

        with self.dbcnxn.open_session() as session:

            static_with_sensor_readings = (
                session.query(*columns)
                .join(
                    sensor_readings,
                    (static_features.c.point_id == sensor_readings.c.point_id)
                    & (
                        static_features.c.measurement_start_utc
                        == sensor_readings.c.measurement_start_utc
                    )
                    & (
                        static_features.c.species_code == sensor_readings.c.species_code
                    ),
                    isouter=True,
                )
                .filter(static_features.c.source == source.value)
                .order_by(
                    static_features.c.point_id,
                    static_features.c.feature_name,
                    static_features.c.measurement_start_utc,
                    sensor_readings.c.species_code,
                )
            )

            return static_with_sensor_readings

    @db_query
    def get_training_data_inputs(
        self,
        start_date: datetime,
        end_date: datetime,
        species: List[Species],
        point_ids: List[str],
        features: List[FeatureNames],
        source: Source,
    ):
        """Query the database to get inputs for model fitting."""

        self.logger.info(
            "Loading training data for species: %s from sources: %s",
            [s.value for s in species],
            source.value,
        )
        self.logger.info(
            "Loading data from %s (inclusive) to %s (exclusive)", start_date, end_date,
        )

        # Get sensor readings and summary of available data from start_date (inclusive) to end_date
        static_features = self.get_static_features(
            start_date,
            end_date,
            features,
            source,
            point_ids,
            species,
            output_type="subquery",
        )

        if source == Source.laqn:
            sensor_readings = self.get_laqn_readings(
                start_date, end_date, species, output_type="subquery"
            )
        elif source == Source.aqe:
            sensor_readings = self.get_aqe_readings(
                start_date, end_date, species, output_type="subquery"
            )
        elif source == Source.satellite:
            sensor_readings = self.get_satellite_readings(
                start_date, end_date, species, output_type="subquery"
            )

        # static_with_sensors = self.join_features_to_sensors(
        #     static_features, sensor_readings, source, output_type="sql"
        # )

        return self.join_features_to_sensors(
            static_features, sensor_readings, source, output_type="query",
        )

    @db_query
    def get_prediction_data_inputs(
        self,
        start_date: datetime,
        end_date: datetime,
        point_ids: List[str],
        features: List[FeatureNames],
        source: Source,
    ):
        """Query the database to get inputs for model fitting."""

        self.logger.info(
            "Loading prediction data for source: %s", source.value,
        )
        self.logger.info(
            "Loading data from %s (inclusive) to %s (exclusive)", start_date, end_date,
        )

        # Get sensor readings and summary of available data from start_date (inclusive) to end_date
        static_features = self.get_static_features(
            start_date, end_date, features, source, point_ids, output_type="subquery"
        )

        with self.dbcnxn.open_session() as session:

            return (
                session.query(
                    static_features.c.point_id,
                    static_features.c.measurement_start_utc,
                    static_features.c.feature_name,
                    static_features.c.value_1000,
                    static_features.c.value_500,
                    static_features.c.value_200,
                    static_features.c.value_100,
                    static_features.c.value_10,
                    static_features.c.lat,
                    static_features.c.lon,
                )
                .filter(static_features.c.source == source.value)
                .order_by(
                    static_features.c.point_id,
                    static_features.c.feature_name,
                    static_features.c.measurement_start_utc,
                )
            )

    def get_training_satellite_inputs(self):
        """Get satellite inputs"""
        train_start_date = self.config["train_start_date"]
        train_end_date = self.config["train_end_date"]
        pred_start_date = self.config["pred_start_date"]
        pred_end_date = self.config["pred_end_date"]
        sources = ["satellite"]
        species = self.config["species"]
        point_ids = self.config["train_satellite_interest_points"]
        features = self.config["feature_names"]

        if len(species) > 1 and species[0] != "NO2":
            raise NotImplementedError(
                "Can only request NO2 for Satellite at present. ModelData class needs to handle this"
            )

        self.logger.info(
            "Getting Satellite training data for species: %s, from %s (inclusive) to %s (exclusive)",
            species,
            train_start_date,
            pred_end_date,
        )

        # Get model features between train_start_date and pred_end_date
        all_features = self.get_model_features(
            train_start_date, pred_end_date, features, sources, point_ids
        )
        # Get satellite readings
        sat_train_df = self.get_satellite_readings_training(
            train_start_date, train_end_date, species=species, output_type="df"
        )
        sat_pred_df = self.get_satellite_readings_pred(
            pred_start_date, pred_end_date, species=species, output_type="df"
        )
        satellite_readings = pd.concat([sat_train_df, sat_pred_df], axis=0)

        with self.dbcnxn.open_session() as session:
            sat_site_map_q = session.query(SatelliteGrid)
        sat_site_map_df = pd.read_sql(
            sat_site_map_q.statement, sat_site_map_q.session.bind
        )
        # Convert uuid to strings to allow merge
        all_features["point_id"] = all_features["point_id"].astype(str)
        sat_site_map_df["point_id"] = sat_site_map_df["point_id"].astype(str)

        # Get satellite box id for each feature interest point
        all_features = all_features.merge(sat_site_map_df, how="left", on=["point_id"])

        # Get satellite data
        return all_features, satellite_readings

    @staticmethod
    def join_forecast_on_dataframe(
        data_df: pd.DataFrame,
        pred_dict: TargetDict,
    ):
        """Return a new dataframe with columns updated from pred_dict."""
        # TODO implement this for multiple sources
        # TODO take the index as a parameter and match pred_dict onto data_df using index
        for pollutant in pred_dict:
            data_df[pollutant + "_mean"] = pred_dict[pollutant]["mean"].flatten()
            data_df[pollutant + "_var"] = pred_dict[pollutant]["var"].flatten()
        return data_df

        # if not sources:
        #     sources = pred_dict.keys()
        # if not species:
        #     raise NotImplementedError("Todo")
        # # create new dataframe and track indices for different sources + pollutants
        # indices = []
        # for source in sources:
        #     # for pollutant in pred_dict[source]:
        #     # print(type(source.value))
        #     # print(type(pollutant))
        #     # print(index_dict[source])
        #     # print("Shape of index_dict[source][pollutant]:", index_dict[source.value][pollutant].shape)
        #     indices.extend(index_dict[source])
        # predict_df = pd.DataFrame(index=indices)
        # data_df = data_df.loc[indices]
        # # iterate through NO2_mean, NO2_var, PM10_mean, PM10_var...
        # for pred_type in ["mean", "var"]:
        #     for pollutant in species:
        #         # add a column containing pred results for all sources
        #         column = np.array([])
        #         for source in sources:
        #             column = np.append(column, pred_dict[source][pollutant][pred_type])
        #         predict_df[pollutant + "_" + pred_type] = column
        # # add predict_df as new columns to data_df - they should share an index
        # new_df = pd.concat([data_df, predict_df], axis=1, ignore_index=False)
        # return new_df

    def update_test_df_with_preds(self, test_pred_dict: dict):
        """Update the normalised_pred_data_df with predictions for all pred sources.

        Args:
            test_pred_dict: Dictionary of model predictions.
        """
        self.normalised_pred_data_df = self.get_df_from_pred_dict(
            self.normalised_pred_data_df, self.get_pred_data_arrays(), test_pred_dict,
        )

    def update_training_df_with_preds(self, training_pred_dict):
        """Updated the normalised_training_data_df with predictions on the training set."""
        self.normalised_training_data_df = self.get_df_from_pred_dict(
            self.normalised_training_data_df,
            self.get_training_data_arrays(),
            training_pred_dict,
        )

    def update_remote_tables(
        self, full_config: FullConfig, preprocessing: Optional[Dict] = None
    ):
        """Update the model results table with the model results"""
        data_config = full_config.json(sort_keys=True)
        data_id = full_config.data_id()

        row = dict(
            data_id=self.data_id, data_config=data_config, preprocessing=preprocessing,
        )
        records = [row]
        self.logger.info("Writing data settings to air quality modelling data table.")
        self.commit_records(records, table=AirQualityDataTable, on_conflict="overwrite")
