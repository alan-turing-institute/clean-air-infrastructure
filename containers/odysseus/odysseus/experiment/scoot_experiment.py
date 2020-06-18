"""Experiment for training multiple models on multiple scoot detectors."""

from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
import tensorflow as tf
from cleanair.databases import DBWriter
from cleanair.databases.tables import TrafficInstanceTable, TrafficModelTable
from cleanair.mixins import ScootQueryMixin
from ..dataset import TrafficDataset
from .experiment import ExperimentMixin
from ..modelling import parse_kernel, train_sensor_model

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

    def load_datasets(
        self, detectors: List, start_date: str, end_date: Optional[str] = None,
    ) -> List[tf.data.Dataset]:
        """Load the data and train the models."""
        self.logger.info(
            "Querying the scoot database for readings on %s detectors.", len(detectors)
        )
        scoot_df = self.get_scoot_with_location(
            start_date, end_time=end_date, detectors=detectors, output_type="df"
        )
        # list of scoot datasets
        datasets = [
            TrafficDataset.from_dataframe(
                scoot_df.loc[scoot_df.detector_id.isin(data_config["detectors"])],
                preprocessing,
            )
            for data_config, preprocessing in self.frame[
                ["data_config", "preprocessing"]
            ]
        ]
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
        for row, dataset in zip(self.frame, datasets):
            model_params = row["model_params"]
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
            # TODO: write models to blob storage
            # instance.save_model(
            #     model, os.path.join(args.root, args.experiment, "models"),
            # )
            model_list.append(model)
        return model_list

    def update_remote_tables(self):
        """Update the instance, data and model tables."""
        ExperimentMixin.update_remote_tables(self)
