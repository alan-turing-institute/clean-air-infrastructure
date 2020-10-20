"""Class for evaluating metrics and writing them to the database."""

from datetime import timedelta
from typing import Dict, List, Optional
import pandas as pd
import sklearn
from sqlalchemy import inspect
from ..databases import DBWriter, Base
from ..databases.tables import (
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityModelTable,
    AirQualityResultTable,
    AirQualitySpatialMetricsTable,
    AirQualityTemporalMetricsTable,
)
from ..loggers import get_logger
from ..models import ModelData
from ..mixins import InstanceQueryMixin, ResultQueryMixin
from ..types import FullDataConfig, Source, Species


class AirQualityMetrics(DBWriter, InstanceQueryMixin, ResultQueryMixin):
    """Evaluate metrics for an air quality model.

    Attributes:
        data_config: The data settings for training and forecasting.
        instance_id: The ID of the model fit.
        mae: If true, evaluate the mean absolute error.
        mse: If true, evaluate the mean squared error.
        observation_df: Dataframe of true observations over the train and forecast periods.
        r2_score: If true, evalute the r squared score.
        result_df: Dataframe of results loaded using the instance id.
        spatial_df: Dataframe of metrics for each point_id.
        temporal_df: Dataframe of metrics for each timestamp.
    """

    def __init__(
        self,
        instance_id: str,
        mae: bool = True,
        mse: bool = True,
        r2_score: bool = True,
        secretfile: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(secretfile=secretfile, **kwargs)
        if not hasattr(self, "logger"):
            self.logger = get_logger("Metrics")
        self.instance_id = instance_id
        self.mae = mae
        self.mse = mse
        self.r2_score = r2_score
        instance_df = self.get_instances_with_params(
            instance_ids=[instance_id], output_type="df"
        )
        # check there is an instance in the database with the id passed
        if len(instance_df) == 0:
            raise ValueError("Instance ID %s not in DB. Try a different ID.")

        # create a data config that only downloads laqn data
        self.data_config = FullDataConfig(**instance_df.at[0, "data_config"])
        self.data_config = keep_only_laqn_from_data_config(self.data_config)

        # empty dataframe for spatial metrics
        self.spatial_df = pd.DataFrame(
            columns=get_columns_of_table(AirQualitySpatialMetricsTable)
        )
        # empty dataframe for temporal metrics
        self.temporal_df = pd.DataFrame(
            columns=get_columns_of_table(AirQualityTemporalMetricsTable)
        )

    @property
    def result_table(self) -> AirQualityResultTable:
        """The air quality result table."""
        return AirQualityResultTable

    @property
    def model_table(self) -> AirQualityModelTable:
        """The air quality model parameters table."""
        return AirQualityModelTable

    @property
    def data_table(self) -> AirQualityDataTable:
        """The air quality data config table."""
        return AirQualityDataTable

    @property
    def instance_table(self) -> AirQualityInstanceTable:
        """The air quality instance table."""
        return AirQualityInstanceTable

    def load_observation_df(self, model_data: ModelData) -> pd.DataFrame:
        """Load the observations for the train and test period."""
        # download only laqn data
        self.logger.info("Reading training and test data to compare against predictions.")
        train_df: pd.DataFrame = model_data.download_config_data(self.data_config)[Source.laqn]
        test_df: pd.DataFrame = model_data.download_config_data(self.data_config, training_data=False)[Source.laqn]

        # join train and test dataframes
        train_df["forecast"] = False
        test_df["forecast"] = True
        observation_df: pd.DataFrame = pd.concat(
            [train_df, test_df], ignore_index=True
        )
        observation_df = preprocess_dataframe_types(observation_df)
        return observation_df

    def load_result_df(self) -> None:
        """Load the results for the instance."""
        self.logger.info("Reading results for LAQN for instance %s.", self.instance_id)
        result_df = self.query_results(
            self.instance_id, Source.laqn, output_type="df", with_location=False,
        )
        return preprocess_dataframe_types(result_df)

    def __evaluate_group(
        self, group_df: pd.DataFrame, pollutant: Species
    ) -> Dict[str, float]:
        """Given a group run the metrics."""
        group_metrics = dict(
            instance_id=group_df.instance_id.iloc[0],
            data_id=group_df.data_id.iloc[0],
            source=Source.laqn.value,
            pollutant=pollutant.value,
        )
        if self.mae:
            group_metrics["mae"] = sklearn.metrics.mean_absolute_error(
                group_df[pollutant.value], group_df[pollutant.value + "_mean"]
            )
        if self.mse:
            group_metrics["mse"] = sklearn.metrics.mean_squared_error(
                group_df[pollutant.value], group_df[pollutant.value + "_mean"]
            )
        if self.r2_score:
            group_metrics["r2_score"] = sklearn.metrics.r2_score(
                group_df[pollutant.value], group_df[pollutant.value + "_mean"]
            )
        return group_metrics

    def evaluate_temporal_metrics(self, observation_df: pd.DataFrame, result_df: pd.DataFrame) -> None:
        """Evaluate metrics by grouping by the datetime."""
        joined_df = observation_df.merge(
            result_df, on=["point_id", "measurement_start_utc"], how="inner"
        )
        self.logger.info(
            "Evaluating metrics temporally - group by datetime and calculate metrics across each time slice."
        )
        groups = joined_df.groupby(["measurement_start_utc", "forecast"])
        metrics_records = list()
        for (timestamp, forecast), group_df in groups:
            for pollutant in self.data_config.species:
                if len(group_df) == 0:
                    continue
                row = self.__evaluate_group(group_df, pollutant)
                row["measurement_start_utc"] = timestamp
                row["measurement_end_utc"] = timestamp + timedelta(hours=1)
                row["forecast"] = forecast
                metrics_records.append(row)
        self.temporal_df = pd.DataFrame(metrics_records)
        self.logger.info(
            "%s rows in the temporal metrics dataframe.", len(self.temporal_df)
        )

    def evaluate_spatial_metrics(self, observation_df: pd.DataFrame, result_df: pd.DataFrame) -> None:
        """Evaluate metrics by grouping by point id."""
        self.logger.debug(
            "Columns in left (observation) df %s", list(observation_df.columns)
        )
        self.logger.debug(
            "Columns in right (result) df %s", list(result_df.columns)
        )
        joined_df = observation_df.merge(
            result_df, on=["point_id", "measurement_start_utc"], how="inner",
        )
        self.logger.debug(joined_df)
        self.logger.info(
            "Evaluating metrics spatially - group by point_id and calculate metrics for each sensor."
        )
        groups = joined_df.groupby(["point_id", "forecast"])
        metrics_records = list()
        for (point_id, forecast), group_df in groups:
            for pollutant in self.data_config.species:
                if len(group_df) == 0:
                    continue
                row = self.__evaluate_group(group_df, pollutant)
                row["point_id"] = point_id
                row["forecast"] = forecast
                metrics_records.append(row)
        self.spatial_df = pd.DataFrame(metrics_records)
        self.logger.info(
            "%s rows in the spatial metrics dataframe.", len(self.spatial_df)
        )

    def update_remote_tables(self):
        """Write the metrics to the air quality modelling schema."""
        self.logger.info("Writing the metrics for space and time to the database.")
        spatial_records = self.spatial_df[
            get_columns_of_table(AirQualitySpatialMetricsTable)
        ].to_dict("records")
        temporal_records = self.temporal_df[
            get_columns_of_table(AirQualityTemporalMetricsTable)
        ].to_dict("records")
        self.commit_records(
            spatial_records,
            on_conflict="overwrite",
            table=AirQualitySpatialMetricsTable,
        )
        self.commit_records(
            temporal_records,
            on_conflict="overwrite",
            table=AirQualityTemporalMetricsTable,
        )

def get_columns_of_table(table: Base) -> List[str]:
    """Get the column names of a table."""
    table_inst = inspect(table)
    return [c_attr.key for c_attr in table_inst.mapper.column_attrs]


def remove_rows_with_nans(joined_df: pd.DataFrame, species: List[Species]):
    """Remove rows with NaN as an observation."""
    cols_to_check = species.copy()
    cols_to_check.extend(map(lambda x: x.value + "_mean", cols_to_check))
    return joined_df.loc[joined_df[cols_to_check].dropna().index]

def keep_only_laqn_from_data_config(data_config: FullDataConfig) -> FullDataConfig:
    """Only keep the laqn source and interest points from the data config."""
    data_config.train_sources = [Source.laqn]
    data_config.train_interest_points = {Source.laqn: data_config.train_interest_points[Source.laqn]}
    data_config.pred_sources = [Source.laqn]
    data_config.pred_interest_points = {Source.laqn: data_config.pred_interest_points[Source.laqn]}
    return data_config

def preprocess_dataframe_types(dframe: pd.DataFrame) -> pd.DataFrame:
    """Convert datetimes to utc and ensure point ids are strings."""
    # ensure point ids are both strings
    dframe["point_id"] = dframe.point_id.apply(str)
    # ensure both datetimes are utc
    dframe["measurement_start_utc"] = pd.to_datetime(
        dframe.measurement_start_utc, utc=True
    )
    return dframe
