"""Vizualise available sensor data for a model fit"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple, overload
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from nptyping import NDArray, Float64
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, text, column, String
from sqlalchemy.sql.expression import Alias
from ..databases.tables import (
    StaticFeature,
    MetaPoint,
)
from ..databases import DBReader
from ..databases.base import Values
from ..mixins import DBQueryMixin
from ..loggers import get_logger
from ..decorators import db_query

from ..types import (
    FullConfig,
    Source,
    Species,
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
    """Return x if it has length=1"""
    if len(x) == 1:
        return x
    raise ValueError(
        """Pandas pivot table trying to return an array of values.
                        Here it must only return a single value"""
    )


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

    def x_names_norm(self, x_names):
        """Get the normalised x names"""
        return [x + "_norm" for x in x_names]

    @staticmethod
    def join_forecast_on_dataframe(
        data_df: pd.DataFrame, pred_dict: TargetDict, index: NDArray
    ):
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

    # pylint: disable=R0913
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

            train_end_date = full_config.train_end_date
            if source == Source.satellite:
                train_end_date = full_config.pred_end_date

            data_output[source] = self.download_source_data(
                with_sensor_readings=True,
                start_date=full_config.train_start_date,
                end_date=train_end_date,
                species=full_config.species,
                point_ids=full_config.train_interest_points[source],
                features=full_config.features,
                source=source,
            )
        return data_output

    def download_prediction_config_data(
        self, full_config: FullConfig
    ) -> Dict[Source, pd.DataFrame]:
        """Download prediction data"""
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

    @db_query
    def select_static_features(self, features: List[FeatureNames], source: Source):

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
            features, source, output_type="subquery"
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
