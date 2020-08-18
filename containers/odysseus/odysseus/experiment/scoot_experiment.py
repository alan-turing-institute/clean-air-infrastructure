"""Experiment for training multiple models on multiple scoot detectors."""

from __future__ import annotations
from typing import List, Optional, Tuple, TYPE_CHECKING
import tensorflow as tf
from cleanair.databases import DBWriter
from cleanair.databases.tables import TrafficInstanceTable, TrafficModelTable
from cleanair.utils import save_model
from cleanair.mixins import ScootQueryMixin
from ..dataset import ScootDataset
from .experiment import ExperimentMixin
from ..modelling import parse_kernel, train_sensor_model
from .utils import save_gpflow2_model_to_file

if TYPE_CHECKING:
    import gpflow


class ScootExperiment(ScootQueryMixin, ExperimentMixin, DBWriter):
    """Experiment for scoot modelling."""

    @property
    def instance_table(self) -> TrafficInstanceTable:
        """Traffic instance table."""
        return TrafficInstanceTable

    @property
    def model_table(self) -> TrafficModelTable:
        """Traffic model table."""
        return TrafficModelTable

    # XXX - Can get this info direct from data_config
    def load_datasets(
        self, detectors: List[str], start: str, upto: Optional[str] = None,
    ) -> List[ScootDataset]:
        """Load the data and train the models."""
        self.logger.info(
            "Querying the scoot database for readings on %s detectors.", len(detectors)
        )
        scoot_df = self.scoot_readings(
            detectors=detectors, start=start, upto=upto, output_type="df", with_location=True,
        )
        if scoot_df.empty:
            raise ValueError('No readings in SCOOT dataframe')

        # list of scoot datasets
        datasets = self.frame[["data_config", "preprocessing"]].apply(
            lambda x, y: ScootDataset(x, y, dataframe=scoot_df)
        )
        # for data_config, preprocessing in zip(self.frame.data_config, self.frame.preprocessing):
        #     processed = ScootDataset.preprocess_dataframe(
        #         scoot_df.loc[scoot_df.detector_id.isin(data_config["detectors"])].copy(),
        #         preprocessing
        #     )
        #     datasets.append(
        #         ScootDataset.from_dataframe(processed, preprocessing)
        #     )
        return datasets

    def train_models(
        self,
        datasets: List[tf.data.Dataset],
        dryrun: Optional[bool] = False,
        logging_freq: Optional[int] = 100,
    ) -> List[gpflow.models.GPModel]:
        """Train GPs on the datasets.

        Args:
            datasets: Datasets loaded from scoot data.

        Returns:
            List of trained GPs.
        """
        model_list = []
        # loop over datasets training models and saving the trained models
        for i, dataset in enumerate(datasets):
            row = self.frame.iloc[i]

            model_params = row["model_param"]
            preprocessing = row["preprocessing"]
            num_features = len(preprocessing["features"])
            X = tf.stack([element[:num_features] for element in dataset])
            Y = tf.stack([element[num_features:] for element in dataset])
            self.logger.info("Training model on instance %s", row["instance_id"])
            # get a kernel from settings
            if dryrun:
                continue
            optimizer = tf.keras.optimizers.Adam(0.001)
            kernel = parse_kernel(model_params["kernel"])  # returns gpflow kernel
            model = train_sensor_model(
                X,
                Y,
                kernel,
                optimizer,
                maxiter=model_params["maxiter"],
                logging_freq=logging_freq,
                n_inducing_points=model_params["n_inducing_points"],
                inducing_point_method=model_params["inducing_point_method"],
            )
            save_model(row["instance_id"], model, save_gpflow2_model_to_file)
            model_list.append(model)
        return model_list

    def update_remote_tables(self):
        """Update the instance, data and model tables."""
        ExperimentMixin.update_remote_tables(self)
