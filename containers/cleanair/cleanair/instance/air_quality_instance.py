"""Air quality instance."""

from .instance import Instance
from ..databases.tables import (
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityModelTable,
)
from ..types import DataConfig
from ..types.model_types import ParamsDict


class AirQualityInstance(Instance):
    """A model instance on air quality data."""

    def update_model_tables(self, model_params: ParamsDict) -> None:
        """Write the model_params to the air quality model table.

        Args:
            model_params: All the parameters of the model.
        """
        self.logger.info("Writing model parameters to the air quality modelling table.")
        records = [
            dict(
                model_name=self.model_name,
                param_id=self.param_id,
                model_param=model_params,
            )
        ]
        self.commit_records(records, on_conflict="ignore", table=AirQualityModelTable)

    def update_data_tables(self, data_config: DataConfig) -> None:
        """Write the data parameters to the air quality data table.

        Args:
            data_config: The dictionary of data settings.
        """
        self.logger.info("Writing data config to the air quality data table.")
        records = [
            dict(data_id=self.data_id, data_config=data_config, preprocessing=dict(),)
        ]
        self.commit_records(records, on_conflict="ignore", table=AirQualityDataTable)

    def update_remote_tables(self):
        """Write instance to the air quality instance table."""
        self.logger.info("Writing the instance to the air quality instance table.")
        records = [self.to_dict()]
        self.commit_records(
            records, on_conflict="ignore", table=AirQualityInstanceTable
        )
