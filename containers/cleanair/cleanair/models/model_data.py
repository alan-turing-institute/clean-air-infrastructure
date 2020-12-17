"""Vizualise available sensor data for a model fit"""
from __future__ import annotations
import sys
from typing import Dict, List, Tuple, overload, Callable
from datetime import datetime, timedelta
from itertools import groupby
import pandas as pd
import numpy as np
from nptyping import NDArray, Float64
from pydantic import ValidationError
from sqlalchemy import func, text, column, String, cast, and_
from sqlalchemy.sql.expression import Alias
from sqlalchemy.dialects.postgresql import UUID
from ..databases.tables import (
    StaticFeature,
    MetaPoint,
)
from ..databases import DBReader
from ..databases.base import Values
from ..mixins import DBQueryMixin
from ..loggers import get_logger, green
from ..decorators import db_query

from ..types import (
    FullDataConfig,
    Source,
    Species,
    FeatureNames,
    FeaturesDict,
    IndexedDatasetDict,
    TargetDict,
)
from .schemas import (
    StaticFeatureTimeSpecies,
    StaticFeatureLocSchema,
    StaticFeaturesWithSensors,
)

# pylint: disable=too-many-lines

ONE_HOUR_INTERVAL = text("interval '1 hour'")
ONE_DAY_INTERVAL = text("interval '1 day'")


def flatten_dict(dict_list):
    "Concatenate a list of dictionaries into a single dictionary"
    return {k: v for d in dict_list for k, v in d.items()}


def split_apply_combine(function, key: Callable, iterable: List[Dict]):
    """
    Split list_of_dicts by grouping key and then apply function to each group
    and returning a new list of dictionaries
    """

    # Sort the input
    iterable.sort(key=key)
    groups = groupby(iterable, key=key)
    return map(function, map(lambda x: x[1], groups))


class ModelDataExtractor:
    """Extract model data"""

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

    def __norm_stats(
        self, full_config: FullDataConfig, data_frames: Dict[str, pd.DateFrame]
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

    @staticmethod
    def __x_names_norm(x_names):
        """Get the normalised x names"""
        return [x + "_norm" for x in x_names]

    def normalize_data(
        self, full_config: FullDataConfig, data_frames: Dict[str, pd.DateFrame]
    ) -> Dict[str, pd.DateFrame]:
        """Normalise the x columns"""

        norm_mean, norm_std = self.__norm_stats(full_config, data_frames)

        x_names_norm = self.__x_names_norm(full_config.x_names)

        data_output: Dict[str, pd.DateFrame] = {}
        for source, data_df in data_frames.items():

            data_df_normed = data_df.copy()

            data_df_normed[x_names_norm] = (
                data_df_normed[full_config.x_names] - norm_mean
            ) / norm_std

            data_output[source] = data_df_normed

        return data_output

    # pylint: disable=C0116,R0201
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
        full_config: FullDataConfig,
        data_frame_dict: Dict[Source, pd.DataFrame],
        prediction: bool = False,
    ) -> IndexedDatasetDict:

        species = full_config.species
        x_names = self.__x_names_norm(full_config.x_names)
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

    @staticmethod
    def join_forecast_on_dataframe(data_df: pd.DataFrame, pred_dict: TargetDict):
        """Return a new dataframe with columns updated from pred_dict."""
        # TODO implement this for multiple sources
        # TODO take the index as a parameter and match pred_dict onto data_df using index
        for pollutant in pred_dict:
            # print(pollutant)
            # print(index)
            # print(index_dict[pollutant])
            data_df[pollutant + "_mean"] = pred_dict[pollutant]["mean"].flatten()
            data_df[pollutant + "_var"] = pred_dict[pollutant]["var"].flatten()
        return data_df


#  pylint: disable=R0904
class ModelData(ModelDataExtractor, DBReader, DBQueryMixin):
    """Read data from multiple database tables in order to get data for model fitting"""

    def __init__(self, **kwargs):
        """
        Initialise a ModelData class
        """
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    def download_config_data(
        self, full_config: FullDataConfig, training_data: bool = True
    ) -> Dict[Source, pd.DateFrame]:
        """Download all input data specified in a validated full config file
        by calling self.download_config_data() for all sources

        Args:
            full_config: A configuration class
            training_data: When True get training data, else get prediction data
                Defaults to True. However, if the source  is Satellite it always gets sensor
                readings regardless of this flag
        """

        start_date = (
            full_config.train_start_date
            if training_data
            else full_config.pred_start_date
        )
        end_date = (
            full_config.train_end_date if training_data else full_config.pred_end_date
        )
        sources = (
            full_config.train_sources if training_data else full_config.pred_sources
        )
        point_ids = (
            full_config.train_interest_points
            if training_data
            else full_config.pred_interest_points
        )

        data_output: Dict[Source, pd.DateFrame] = {}
        for source in sources:
            self.logger.info(
                "Downloading source: %s. Training data: %s",
                green(source),
                green(training_data),
            )
            # Satellite data is only a training option  and gets all data from training to prediction
            _end_date = (
                end_date if source != Source.satellite else full_config.pred_end_date
            )
            data_output[source] = self.__download_config_data(
                with_sensor_readings=training_data,
                start_date=start_date,
                end_date=_end_date,
                species=full_config.species,
                point_ids=point_ids[source],
                features=full_config.features,
                source=source,
            )
        return data_output

    def download_forecast_data(
        self, full_config: FullDataConfig
    ) -> Dict[Source, pd.DateFrame]:
        """Download the readings for a forecast period. Used for calculating metrics."""
        data_output: Dict[Source, pd.DataFrame] = {}
        for source in full_config.pred_sources:
            self.logger.info("Downloading source %s forecast data.", source.value)
            data_output[source] = self.__download_config_data(
                with_sensor_readings=True,
                start_date=full_config.pred_start_date,
                end_date=full_config.pred_end_date,
                species=full_config.species,
                point_ids=full_config.pred_interest_points[source],
                features=full_config.features,
                source=source,
            )
        return data_output

    # pylint: disable=R0913
    def __download_config_data(
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
            f_get_data = self.get_static_with_sensors
        else:
            f_get_data = self.get_static_features

        try:
            source_data = f_get_data(
                start_date=start_date,
                end_date=end_date,
                point_ids=point_ids,
                features=features,
                source=source,
                species=species,
                output_type="all",
            )
        except ValidationError:
            self.logger.error(
                "Failed to download static features. This could mean that feature processing needs to be re-ran"
            )
            sys.exit()

        # Get dictionaries of wide data
        self.logger.debug("Postprocessing downloaded data")
        source_data_dicts = [i.dict_flatten(exclude={"source"}) for i in source_data]

        # Create a dataframe from a list of dictionaries
        # pylint: disable=W0108
        wide_pd = pd.DataFrame(
            list(
                split_apply_combine(
                    lambda x: flatten_dict(x),
                    lambda x: (x["point_id"], x["measurement_start_utc"]),
                    source_data_dicts,
                )
            )
        )
        return wide_pd

    @db_query(model=StaticFeatureTimeSpecies)
    def get_static_features(
        self,
        start_date: datetime,
        end_date: datetime,
        features: List[FeatureNames],
        source: Source,
        point_ids: List[str],
        species: List[Species],
    ) -> pd.DateFrame:
        """
        Query the database for static features
            and then cross join with the datetime range and
            species requested.
        """

        static_features = self.select_static_features(
            point_ids, features, source, output_type="subquery"
        )

        static_features_expand = self.__expand_time_species(
            static_features, start_date, end_date, species
        )

        return static_features_expand

    @db_query(StaticFeatureLocSchema)
    def select_static_features(
        self, point_ids: List[str], features: List[FeatureNames], source: Source
    ):
        """
        Return static features from the database for a list of point ids
            for a particular source.
        If point ids are not of the correct source they will not be returned
        Ensures that we always get all point id rows, even if they are not in the database
            (all other columns will be null), by doing an outer join

        Args:
            features: A list of [FeatureNames]
            source: A [Source] (e.g. Source.laqn)
        """

        with self.dbcnxn.open_session() as session:

            # Get a row with all the point ids requested
            point_id_sq = session.query(
                Values(
                    [column("point_id", String),],
                    *[(point_id,) for point_id in point_ids],
                    alias_name="point_ids",
                )
            ).subquery()

            feature_sq = session.query(
                Values(
                    [column("feature_name", String),],
                    *[(feature.value,) for feature in features],
                    alias_name="features",
                )
            ).subquery()

            point_id_feature_cross_join_sq = session.query(
                point_id_sq, feature_sq
            ).subquery()

            london_boundary = self.query_london_boundary(output_type="subquery")

            static_features_with_loc_sq = (
                session.query(
                    StaticFeature.point_id,
                    StaticFeature.feature_name,
                    MetaPoint.source,
                    StaticFeature.value_1000,
                    StaticFeature.value_500,
                    StaticFeature.value_200,
                    StaticFeature.value_100,
                    StaticFeature.value_10,
                    func.ST_X(MetaPoint.location).label("lon"),
                    func.ST_Y(MetaPoint.location).label("lat"),
                    func.ST_Within(MetaPoint.location, london_boundary.c.geom).label(
                        "in_london"
                    ),
                )
                .join(MetaPoint, MetaPoint.id == StaticFeature.point_id, isouter=True,)
                .filter(
                    MetaPoint.id.in_(point_ids),
                    StaticFeature.feature_name.in_(features),
                    MetaPoint.source == source,
                )
                .subquery()
            )

            return session.query(
                cast(point_id_feature_cross_join_sq.c.point_id, UUID).label("point_id"),
                point_id_feature_cross_join_sq.c.feature_name,
                static_features_with_loc_sq.c.source,
                static_features_with_loc_sq.c.value_1000,
                static_features_with_loc_sq.c.value_500,
                static_features_with_loc_sq.c.value_200,
                static_features_with_loc_sq.c.value_100,
                static_features_with_loc_sq.c.value_10,
                static_features_with_loc_sq.c.lon,
                static_features_with_loc_sq.c.lat,
                static_features_with_loc_sq.c.in_london,
            ).join(
                static_features_with_loc_sq,
                and_(
                    (
                        static_features_with_loc_sq.c.point_id
                        == cast(point_id_feature_cross_join_sq.c.point_id, UUID)
                    ),
                    (
                        static_features_with_loc_sq.c.feature_name
                        == point_id_feature_cross_join_sq.c.feature_name
                    ),
                ),
                isouter=True,
            )

    @db_query()
    def __expand_time_species(
        self,
        subquery: Alias,
        start_date: datetime,
        end_date: datetime,
        species: List[Species],
    ):
        """
        Cross product of a date range, a list of species and a subquery
        """

        with self.dbcnxn.open_session() as session:

            cols = [
                func.generate_series(
                    start_date.isoformat(),
                    (end_date - timedelta(hours=1)).isoformat(),
                    ONE_HOUR_INTERVAL,
                ).label("measurement_start_utc"),
                subquery,
            ]

            cols.append(
                Values(
                    [column("species_code", String),],
                    *[(polutant.value,) for polutant in species],
                    alias_name="t2",
                )
            )

            return session.query(*cols)

    @db_query(StaticFeaturesWithSensors)
    def get_static_with_sensors(
        self,
        start_date: datetime,
        end_date: datetime,
        species: List[Species],
        point_ids: List[str],
        features: List[FeatureNames],
        source: Source,
    ):
        """Get static features with sensor readings joined"""

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
        else:
            raise ValueError(
                f"Source must be one of {[Source.laqn, Source.aqe, Source.satellite]}"
            )

        return self.join_features_to_sensors(static_features, sensor_readings, source,)

    @db_query(StaticFeaturesWithSensors)
    def join_features_to_sensors(
        self, static_features: Alias, sensor_readings: Alias, source: Source,
    ):
        """Join sensor readings and static features"""
        columns = [
            static_features.c.point_id,
            static_features.c.measurement_start_utc,
            static_features.c.feature_name,
            static_features.c.source,
            static_features.c.value_1000,
            static_features.c.value_500,
            static_features.c.value_200,
            static_features.c.value_100,
            static_features.c.value_10,
            static_features.c.lat,
            static_features.c.lon,
            static_features.c.in_london,
            static_features.c.species_code,
            sensor_readings.c.value,
        ]

        if source == Source.satellite:
            columns.append(sensor_readings.c.box_id)

        with self.dbcnxn.open_session() as session:

            static_with_sensor_readings = (
                session.query(*columns)
                .join(
                    sensor_readings,
                    and_(
                        and_(
                            static_features.c.point_id == sensor_readings.c.point_id,
                            static_features.c.measurement_start_utc
                            == sensor_readings.c.measurement_start_utc,
                        ),
                        static_features.c.species_code
                        == sensor_readings.c.species_code,
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
