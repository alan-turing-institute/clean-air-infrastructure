"""
A dataset for scoot.
"""
from __future__ import annotations
from typing import Collection, List, Optional
import tensorflow as tf
import numpy as np
import pandas as pd
from nptyping import NDArray, Float64
from cleanair.databases import DBReader
from cleanair.utils import hash_dict
from cleanair.mixins import ScootQueryMixin
from ..preprocess import transform_datetime
from .scoot_config import ScootConfig, ScootPreprocessing


class ScootDataset(DBReader, ScootQueryMixin):
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
            # assign list of detectors if it doesn't exist already
            if not self.data_config.detectors:
                self._data_config.detectors = list(scoot_df.detector_id.unique())
        elif isinstance(dataframe, pd.DataFrame):
            # filter dataframe by start and upto datetime
            scoot_df = dataframe.loc[
                (dataframe.measurement_start_utc >= data_config.start)
                & (dataframe.measurement_start_utc < data_config.upto)
            ]
            # filter dataframe by detector list
            if data_config.detectors:
                scoot_df = scoot_df.loc[
                    dataframe.detector_id.isin(data_config.detectors)
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
    def features_numpy(self) -> NDArray[Float64]:
        """The features as a numpy array."""
        return self.dataframe[self.preprocessing.features].to_numpy(dtype=np.float64)

    @property
    def features_tensor(self) -> tf.Tensor:
        """The feature tensor."""
        return tf.convert_to_tensor(self.features_numpy, dtype=tf.dtypes.float64)

    @property
    def preprocessing(self) -> ScootPreprocessing:
        """A dictionary of preprocessing settings."""
        return self._preprocessing

    @property
    def target_numpy(self) -> NDArray[Float64]:
        """The target as a numpy array."""
        return self.dataframe[self.preprocessing.target].to_numpy(dtype=np.float64)

    @property
    def target_tensor(self) -> tf.Tensor:
        """The target tensor."""
        return tf.convert_to_tensor(self.target_numpy, dtype=tf.dtypes.float64)

    def split_by_detector(self) -> List:
        """Return a list of scoot datasets. One dataset for each detector."""
        datasets = []
        for detector_id in self.data_config.detectors:
            data_config = ScootConfig(
                detectors=[detector_id],
                start=self.data_config.start,
                upto=self.data_config.upto,
            )
            datasets.append(
                ScootDataset(data_config, self.preprocessing, dataframe=self.dataframe)
            )
        return datasets

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
        dataframe: pd.DataFrame, preprocessing: ScootPreprocessing
    ) -> pd.DataFrame:
        """
        Return a dataframe that has been normalised and preprocessed.

        Args:
            dataframe: Raw Scoot data.
            preprocessing: Settings for preprocessing the dataframe.

        Returns:
            Preprocessed traffic data.
        """

        dataframe = transform_datetime(
            dataframe,
            col="measurement_start_utc",
            normalise_datetime=preprocessing.normalise_datetime,
            transformation=preprocessing.datetime_transformation,
        )
        return dataframe
