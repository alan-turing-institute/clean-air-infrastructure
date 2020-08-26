"""Class for evaluating metrics and writing them to the database."""

from datetime import timedelta
import json
from typing import Dict, List, Optional
import pandas as pd
import sklearn
from sqlalchemy import inspect
from ..databases import DBWriter, Base
from ..databases.tables import (
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

        # load the result and instance dataframes from DB
        self.logger.info("Reading results for LAQN for instance %s.", self.instance_id)
        self.result_df: pd.DataFrame = self.query_results(
            instance_id, Source.laqn, output_type="df"
        )
        instance_df = self.get_instances_with_params(
            instance_ids=[instance_id], output_type="df"
        )
        # check there is an instance in the database with the id passed
        if len(instance_df) == 0:
            raise ValueError(
                "Instance ID %s was not found in the database. Try a different ID."
            )

        # load the actual observations from the database
        self.logger.info(
            "Reading training and test data to later compare against our predictions."
        )
        self.data_config = FullDataConfig(
            **json.loads(instance_df.at[0, "data_config"])
        )
        model_data = ModelData(secretfile=secretfile)
        test_data = model_data.download_prediction_config_data(self.data_config)
        train_data = model_data.download_training_config_data(self.data_config)

        # NOTE: we only care about evaluating metrics on laqn
        train_df: pd.DataFrame = train_data[Source.laqn]
        test_df: pd.DataFrame = test_data[Source.laqn]
        train_df["forecast"] = False  # split into train and test
        test_df["forecast"] = True
        self.logger.info("Merging the train and test dataframes for LAQN.")
        self.observation_df: pd.DataFrame = pd.concat([train_df, test_df])
        self.spatial_df = pd.DataFrame(
            columns=get_columns_of_table(AirQualitySpatialMetricsTable)
        )
        self.temporal_df = pd.DataFrame(
            columns=get_columns_of_table(AirQualityTemporalMetricsTable)
        )

    @property
    def result_table(self) -> AirQualityResultTable:
        """The air quality result table."""
        return AirQualityResultTable

    def __evaluate_group(
        self, group_df: pd.DataFrame, pollutant: Species
    ) -> Dict[str, float]:
        """Given a group run the metrics."""
        group_metrics = dict(source=Source.laqn.value, pollutant=pollutant.value,)
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

    def evaluate_temporal_metrics(self) -> None:
        """Evaluate metrics by grouping by the datetime."""
        joined_df = self.observation_df.join(
            self.result_df, on=["point_id", "measurement_start_utc"]
        )
        self.logger.info(
            "Evaluating metrics temporally - group by datetime and calculate metrics across each time slice."
        )
        groups = joined_df.groupby(["measurement_start_utc", "forecast"])
        metrics_records = list()
        for (timestamp, forecast), group_df in groups:
            for pollutant in self.data_config.species:
                row = self.__evaluate_group(group_df, pollutant)
                row["measurement_start_utc"] = timestamp
                row["measurement_end_utc"] = timestamp + timedelta(hours=1)
                row["forecast"] = forecast
                metrics_records.append(row)
        self.temporal_df = pd.DataFrame(metrics_records)
        self.logger.info("%s rows in the temporal metrics dataframe.")

    def evaluate_spatial_metrics(self) -> None:
        """Evaluate metrics by grouping by point id."""
        joined_df = self.observation_df.join(
            self.result_df, on=["point_id", "measurement_start_utc"]
        )
        self.logger.info(
            "Evaluating metrics spatially - group by point_id and calculate metrics for each sensor."
        )
        groups = joined_df.groupby(["point_id", "forecast"])
        metrics_records = list()
        for (point_id, forecast), group_df in groups:
            for pollutant in self.data_config.species:
                row = self.__evaluate_group(group_df, pollutant)
                row["point_id"] = point_id
                row["forecast"] = forecast
                metrics_records.append(row)
        self.spatial_df = pd.DataFrame(metrics_records)
        self.logger.info("%s rows in the spatial metrics dataframe.")

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
