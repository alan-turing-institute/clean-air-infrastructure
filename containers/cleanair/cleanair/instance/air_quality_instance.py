"""Air quality instance."""

from typing import Optional
from datetime import datetime
from .air_quality_result import AirQualityResult
from .instance import Instance
from ..databases.tables import (
    AirQualityDataTable,
    AirQualityInstanceTable,
    AirQualityModelTable,
)
from ..models import ModelData, ModelMixin
from ..types import DataConfig
from ..types.model_types import ParamsDict


class AirQualityInstance(Instance):
    """A model instance on air quality data."""

    def update_model_tables(self, model_params: ParamsDict) -> None:
        """Write the model_params to the air quality model table.

        Args:
            model_params: All the parameters of the model.
        """
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
        records = [
            dict(data_id=self.data_id, data_config=data_config, preprocessing=dict(),)
        ]
        self.commit_records(records, on_conflict="ignore", table=AirQualityDataTable)

    def update_remote_tables(self):
        """Write instance to the air quality instance table."""
        records = [self.to_dict()]
        self.commit_records(
            records, on_conflict="ignore", table=AirQualityInstanceTable
        )

    def train(self, model: ModelMixin, dataset: ModelData) -> None:
        """Train the model on a dataset.

        Args:
            model: An instantiated air quality model.
            dataset: Training dataset for air quality.
        """
        training_data_dict = dataset.get_training_data_arrays(dropna=False)
        x_train = training_data_dict["X"]
        y_train = training_data_dict["Y"]

        # train model
        self.logger.info(
            "Training model for %s iterations.", model.model_params["maxiter"]
        )
        self.fit_start_time = datetime.now().isoformat()
        model.fit(x_train, y_train)
        self.logger.info("Training completed")

    def forecast(
        self, model: ModelMixin, dataset: ModelData, secretfile: Optional[str] = None
    ) -> AirQualityResult:
        """Predict using the model on the test dataset.

        Args:
            model: An instantiated air quality model.
            dataset: Training dataset for air quality.

        Returns:
            An air quality result with predictions from the model.
        """
        # predict either at the test set
        predict_data_dict = dataset.get_pred_data_arrays(dropna=False)
        x_test = predict_data_dict["X"]

        # Do prediction
        self.logger.info("Started predicting on the test set.")
        y_pred = model.predict(x_test)
        self.logger.info("Finished predicting")

        dataset.update_test_df_with_preds(y_pred)
        result_df = dataset.normalised_pred_data_df

        # create a results object
        return AirQualityResult(
            self.instance_id, dataset.data_id, result_df, secretfile=secretfile
        )

    def predict_on_training_set(
        self, model: ModelMixin, dataset: ModelData, secretfile: Optional[str] = None
    ) -> AirQualityResult:
        """Predict on the training set using the model.

        Args:
            model: An instantiated air quality model.
            dataset: Training dataset for air quality.

        Returns:
            An air quality result with predictions from the model.
        """
        # get the training dataset
        training_data_dict = dataset.get_training_data_arrays(dropna=False)
        x_train = training_data_dict["X"]

        # predict on the training dataset
        y_pred = model.predict(x_train)

        # update the test dataframe and use this as a result dataframe
        dataset.update_training_df_with_preds(y_pred)
        result_df = dataset.normalised_training_data_df

        # create a results object
        return AirQualityResult(
            self.instance_id, dataset.data_id, result_df, secretfile=secretfile
        )
