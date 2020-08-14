"""
A traffic dataset.
"""

from typing import Collection
import tensorflow as tf
import pandas as pd
from cleanair.databases import DBReader
from cleanair.databases.tables import TrafficDataTable
from cleanair.utils import hash_dict
from cleanair.mixins import ScootQueryMixin
from ..preprocess import normalise_datetime


# TODO Patrick: I don't think this class should inherit from TF dataset
# Instead it should read data from DB and output a TF dataset/pd.DataFrame/np.array
class TrafficDataset(DBReader, ScootQueryMixin, tf.data.Dataset):
    """
    A traffic dataset that queries the database given a data config dictionary.
    """

    def __init__(
        self, data_config: dict, preprocessing: dict, secretfile: str, **kwargs
    ):
        # check the data config dictionary is valid
        TrafficDataset.validate_data_config(data_config)
        TrafficDataset.validate_preprocessing(preprocessing)

        # load a database reader super class
        DBReader.__init__(self, secretfile=secretfile, **kwargs)

        # store the data config - access with property
        self._data_config = data_config
        self._preprocessing = preprocessing

        # load scoot from the data config
        traffic_df = self.scoot_readings(**self.data_config, output_type="df")
        # from dataframe load datatset
        self._df = TrafficDataset.preprocess_dataframe(traffic_df, self._preprocessing)
        self._input_dataset = TrafficDataset.from_dataframe(
            self._df, self._preprocessing
        )

        # pass the variant tensor the init of the Dataset class
        variant_tensor = self._input_dataset._variant_tensor_attr
        tf.data.Dataset.__init__(self, variant_tensor)

    # necessary to overwrite this abstract method
    def _inputs(self):
        return [self._input_dataset]

    @property
    def element_spec(self):
        """Get the element specification of the dataset."""
        return self._input_dataset.element_spec

    @property
    def data_config(self):
        """A dictionary of data settings."""
        return self._data_config

    @property
    def dataframe(self):
        """The dataset dataframe."""
        return self._df

    @property
    def data_id(self):
        """The id of the hashed data config."""
        return TrafficDataset.data_id_from_hash(self.data_config, self.preprocessing)

    @property
    def features_tensor(self):
        """The feature tensor."""
        return tf.stack([element[0] for element in self._input_dataset])

    @property
    def preprocessing(self):
        """A dictionary of preprocessing settings."""
        return self._preprocessing

    @property
    def target_tensor(self):
        """The target tensor."""
        return tf.stack([element[1] for element in self._input_dataset])

    @staticmethod
    def validate_data_config(data_config: dict):
        """
        Checks if the dictionary of data settings passed is valid.

        Args:
            data_config: Settings to load the data.
        """
        value_types = [str, str, list, list]
        min_keys = ["start", "end", "detectors", "weekdays"]
        validate_dictionary(data_config, min_keys, value_types)

    @staticmethod
    def validate_preprocessing(preprocessing: dict):
        """
        Checks if the dictionary passed is valid for preprocessing a traffic dataset.

        Args:
            preprocessing: Settings for preprocessing and normalising the traffic data.

        Raises:
            KeyError: If one of the dictionary keys are missing.
            TypeError: If the type of the values are invalid.
        """
        value_types = [list, list, bool, str]
        min_keys = ["features", "target", "median", "normaliseby"]
        validate_dictionary(preprocessing, min_keys, value_types)

    @staticmethod
    def validate_dataframe(
        traffic_df: pd.DataFrame, features: Collection = None, target: Collection = None
    ):
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
        traffic_df: pd.DataFrame, preprocessing: dict
    ) -> tf.data.Dataset:
        """
        Return a dataset given a traffic dataframe.

        Args:
            traffic_df: Preprocessed traffic data.
            preprocessing: Settings for preprocessing.

        Returns:
            A new tensorflow dataset.
        """
        TrafficDataset.validate_preprocessing(preprocessing)
        TrafficDataset.validate_dataframe(
            traffic_df,
            features=preprocessing["features"],
            target=preprocessing["target"],
        )

        # create numpy arrays of the x and y columns
        x = traffic_df[preprocessing["features"]].to_numpy()
        y = traffic_df[preprocessing["target"]].to_numpy()

        # load the dataset from the numpy arrays
        dataset = tf.data.Dataset.from_tensor_slices((x, y))

        # cast to float 64
        return dataset.map(
            lambda x, y: (tf.cast(x, tf.float64), tf.cast(y, tf.float64))
        )

    @staticmethod
    def preprocess_dataframe(
        traffic_df: pd.DataFrame, preprocessing: dict
    ) -> pd.DataFrame:
        """
        Return a dataframe that has been normalised and preprocessed.

        Args:
            dataframe: Raw Scoot data.
            preprocessing: Settings for preprocessing the dataframe.

        Returns:
            Preprocessed traffic data.
        """
        TrafficDataset.validate_preprocessing(preprocessing)

        # normalisation
        traffic_df = normalise_datetime(traffic_df, wrt=preprocessing["normaliseby"])

        # choose median for robustness to outliers
        if preprocessing["median"]:
            traffic_gb = traffic_df.groupby(preprocessing["features"])
            traffic_df = traffic_gb[
                preprocessing["target"]
            ].median()  # only works for single task
            traffic_df["time_norm"] = traffic_df.index

        return traffic_df

    @staticmethod
    def data_id_from_hash(data_config: dict, preprocessing: dict) -> str:
        """
        Generate an id from the hash of the two settings dictionaries.

        Args:
            data_config: Settings for data.
            preprocessing: Settings for preprocessing and normalising data.

        Returns:
            An unique id given the settings dictionaries.
        """
        # check there are no overlapping keys
        if set(data_config.keys()) & set(preprocessing.keys()):
            raise ValueError(
                "Data config and preprocessing dictionaries should not have overlapping keys."
            )
        merged_dict = {**data_config, **preprocessing}
        return hash_dict(merged_dict)

    def update_remote_tables(self):
        """Update the data config table for traffic."""
        self.logger.info("Updating the traffic data table.")
        records = [
            dict(
                data_id=self.data_id,
                data_config=self.data_config,
                preprocessing=self.preprocessing,
            )
        ]
        self.commit_records(records, on_conflict="ignore", table=TrafficDataTable)


def validate_dictionary(dict_to_check: dict, min_keys: list, value_types: list):
    """
    Check the dictionary contains a minimum set of keys and the value types are as expected.

    Args:
        dict_to_check: A dictionary which will be validated.
        min_keys: The minimum keys that must be in the dict.
        value_types: The types of the dictionary values.

    Raises:
        KeyError: If one of the dictionary keys are missing.
        TypeError: If the type of the values are invalid.

    Notes:
        In python 3.8 type hinting for dictionaries is supported.
        When upgrading to python 3.8 this function should use type hinting.

        Only supports dictionaries with one depth level.
    """
    # check keys are correct
    if not set(min_keys).issubset(dict_to_check):
        missing_keys = set(min_keys) - set(dict_to_check.keys())
        error_message = (
            "The data config dictionary does not contain the following keys: {k}"
        )
        error_message = error_message.format(k=missing_keys)
        raise KeyError(error_message)

    # check the types of the values
    raise_type_error = False
    for key, value in zip(min_keys, value_types):
        if not isinstance(dict_to_check[key], value):
            bad_key = key
            bad_type = type(dict_to_check[key])
            actual_type = value
            break

    # raise a type error is appropriate
    if raise_type_error:
        error_message = (
            "The value for '{key}' must be a {actual_type}. You passed a {bad_type}."
        )
        error_message = error_message.format(
            bad_key=bad_key, bad_type=bad_type, actual_type=actual_type,
        )
        raise TypeError(error_message)
