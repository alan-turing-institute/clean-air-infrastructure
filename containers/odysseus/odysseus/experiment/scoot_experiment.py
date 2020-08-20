"""Experiment for training multiple models on multiple scoot detectors."""

from __future__ import annotations
from datetime import datetime
from typing import Any, List, Optional, Tuple, Union, TYPE_CHECKING
import pandas as pd
import tensorflow as tf
from cleanair.databases import DBWriter
from cleanair.databases.tables import TrafficDataTable, TrafficInstanceTable, TrafficModelTable
from cleanair.utils import get_git_hash, instance_id_from_hash, hash_dict, save_model
from cleanair.mixins import ScootQueryMixin
from .experiment import ExperimentMixin
from ..modelling import parse_kernel, train_sensor_model
from .utils import save_gpflow2_model_to_file

if TYPE_CHECKING:
    import gpflow
    from ..dataset import ScootConfig, ScootDataset, ScootPreprocessing


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

    @property
    def data_config_table(self) -> TrafficDataTable:
        """Traffic data table."""
        return TrafficDataTable

    @staticmethod
    def from_scoot_configs(
        data_config: Union[List[ScootConfig], ScootConfig],
        model_name: Union[List[str], str],
        model_params: Any,  # TODO specify type
        preprocessing: Union[List[ScootPreprocessing], ScootPreprocessing],
        cluster_id: str = "laptop",
        tag: str = "model_per_detector",
    ) -> ScootExperiment:
        """Create a scoot experiment from the data config and model params."""
        frame = pd.DataFrame()
        frame["data_config"] = data_config
        frame["preprocessing"] = preprocessing
        frame["model_name"] = model_name
        frame["model_params"] = model_params
        frame["fit_start_time"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        frame["cluster_id"] = cluster_id
        frame["tag"] = tag
        frame["git_hash"] = get_git_hash()
        frame["param_id"] = frame["model_param"].apply(lambda x: x.param_id())
        frame["data_id"] = frame[["data_config", "preprocessing"]].apply(
            lambda x, y: hash_dict(dict(**x.dict(), **y.dict()))
        )
        frame["instance_id"] = frame.apply(
            lambda x: instance_id_from_hash(x.model_name, x.param_id, x.data_id, x.git_hash), axis=1
        )


    def train_models(
        self,
        datasets: List[ScootDataset],
        optimizer = tf.keras.optimizers.Adam(0.001),
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
            X = dataset.features_tensor
            Y = dataset.target_tensor
            self.logger.info("Training model on instance %s", row["instance_id"])

            if dryrun:
                continue
            # get a kernel from settings
            kernel = parse_kernel(model_params["kernel"])  # returns gpflow kernel

            model = train_sensor_model(
                dataset.features_tensor,
                dataset.target_tensor,
                kernel,
                optimizer,
                maxiter=model_params.maxiter,
                logging_freq=logging_freq,
                n_inducing_points=model_params.n_inducing_points,
                inducing_point_method=model_params.inducing_point_method,
            )
            save_model(model, row["instance_id"], save_gpflow2_model_to_file,
                        # TODO - env var?
                       model_dir="models/",
                       model_name=model_params["model_name"])
            model_list.append(model)
        return model_list

    def update_remote_tables(self):
        """Update the instance, data and model tables."""
        ExperimentMixin.update_remote_tables(self)
