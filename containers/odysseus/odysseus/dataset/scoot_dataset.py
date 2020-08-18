"""
A dataset for scoot.
"""

from typing import Collection, Optional
import tensorflow as tf
import pandas as pd
from cleanair.databases import DBWriter
from cleanair.utils import hash_dict
from cleanair.mixins import ScootQueryMixin
from ..preprocess import normalise_datetime
from .scoot_config import ScootConfig, ScootPreprocessing


class ScootDataset(DBWriter, ScootQueryMixin):
    """
    A scoot dataset that queries the database given a data config dictionary.
    """

    def __init__(
        self,
        data_config: ScootConfig,
        preprocessing: ScootPreprocessing,
        dataframe: Optional[pd.DataFrame] = None,
        secretfile: Optional[str] = None,
        **kwargs,
    ) -> None:

        # store the data config - access with property
        self._data_config = data_config
        self._preprocessing = preprocessing

        if secretfile:
            # load a database reader super class
            super().__init__(secretfile=secretfile, **kwargs)
            # load scoot from the data config
            scoot_df = self.scoot_readings(**self.data_config.dict(), output_type="df")
        elif dataframe:
            scoot_df = dataframe.loc[
                (scoot_df.measurement_start_utc >= data_config.start)
                & (scoot_df.measurement_start_utc < data_config.upto)
                & (scoot_df.detector_id.isin(data_config.detectors))
            ]
        else:
            raise ValueError(
                "Must pass either secretfile or dataframe as an argument to the ScootDataset init."
            )

        # preprocessing with settings from the preprocessing dict
        self._df = ScootDataset.preprocess_dataframe(scoot_df, self._preprocessing)

    @property
    def data_config(self) -> ScootConfig:
        """A dictionary of data settings."""
        return self._data_config

    @property
    def dataframe(self) -> pd.DataFrame:
        """The dataset dataframe."""
        return self._df

    @property
    def data_id(self) -> str:
        """The id of the hashed data config."""
        merged_dict = {**self.data_config.dict(), **self.preprocessing.dict()}
        return hash_dict(merged_dict)

    @property
    def features_tensor(self) -> tf.Tensor:
        """The feature tensor."""
        raise NotImplementedError("TODO - get tensor from dataframe")

    @property
    def preprocessing(self) -> ScootPreprocessing:
        """A dictionary of preprocessing settings."""
        return self._preprocessing

    @property
    def target_tensor(self) -> tf.Tensor:
        """The target tensor."""
        raise NotImplementedError("TODO - get tensor from dataframe")

    @staticmethod
    def validate_dataframe(
        traffic_df: pd.DataFrame, features: Collection = None, target: Collection = None
    ) -> None:
        """
        Check the dataframe passed has the right column names.

        Args:
            traffic_df: Raw traffic data.
            features (Optional): Names of features.
            target (Optional): Names of targets.

        Raises:
            AssertionError: If the dataframe is not valid.
        """
        if not features:
            features = {"time_norm"}
        if not target:
            target = {"n_vehicles_in_interval"}

        # convert string to set
        if isinstance(features, str):
            features = {features}
        if isinstance(target, str):
            target = {target}

        # convert list/iterable to set
        features = set(features)
        target = set(target)

        min_keys = features.union(target)
        try:
            assert min_keys.issubset(traffic_df.columns)
        except AssertionError:
            raise KeyError(
                "{min} is not subset of {col}".format(
                    min=min_keys, col=traffic_df.columns
                )
            )

    @staticmethod
    def from_dataframe(
        traffic_df: pd.DataFrame, preprocessing: ScootPreprocessing
    ) -> tf.data.Dataset:
        """
        Return a dataset given a traffic dataframe.

        Args:
            traffic_df: Preprocessed traffic data.
            preprocessing: Settings for preprocessing.

        Returns:
            A new tensorflow dataset.
        """
        ScootDataset.validate_dataframe(
            traffic_df, features=preprocessing.features, target=preprocessing.target,
        )

        # create numpy arrays of the x and y columns
        x = traffic_df[preprocessing.features].to_numpy()
        y = traffic_df[preprocessing.target].to_numpy()

        # load the dataset from the numpy arrays
        dataset = tf.data.Dataset.from_tensor_slices((x, y))

        # cast to float 64
        return dataset.map(
            lambda x, y: (tf.cast(x, tf.float64), tf.cast(y, tf.float64))
        )

    @staticmethod
    def preprocess_dataframe(
        traffic_df: pd.DataFrame, preprocessing: ScootPreprocessing
    ) -> pd.DataFrame:
        """
        Return a dataframe that has been normalised and preprocessed.

        Args:
            dataframe: Raw Scoot data.
            preprocessing: Settings for preprocessing the dataframe.

        Returns:
            Preprocessed traffic data.
        """

        # TODO normalisation
        # traffic_df = normalise_datetime(traffic_df, wrt=preprocessing.normaliseby)
        return traffic_df

    # def update_remote_tables(self):
    #     """Update the data config table for traffic."""
    #     self.logger.info("Updating the traffic data table.")
    #     records = [
    #         dict(
    #             data_id=self.data_id,
    #             data_config=self.data_config,
    #             preprocessing=self.preprocessing,
    #         )
    #     ]
    #     self.commit_records(records, on_conflict="ignore", table=TrafficDataTable)
