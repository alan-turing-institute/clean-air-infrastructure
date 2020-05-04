"""
A traffic dataset.
"""

import pandas as pd
import tensorflow as tf
from cleanair.databases import DBReader
from cleanair.mixins import ScootQueryMixin
from ..preprocess import normalise_datetime

class TrafficDataset(DBReader, ScootQueryMixin, tf.data.Dataset):
    """
    A traffic dataset that queries the database given a data config dictionary.
    """

    def __init__(self, data_config: dict, secretfile: str, **kwargs):
        TrafficDataset.validate_data_config(data_config)
        DBReader.__init__(self, secretfile=secretfile, **kwargs)
        self._data_config = data_config
        self._df = self.get_scoot_with_location(
            self._data_config["start"],
            end_time=self._data_config["end"],
            detectors=self._data_config["detectors"],
            output_type="df",
        )
        self._df = normalise_datetime(self._df)
        x = self._df[data_config["x_cols"]].to_numpy()
        y = self._df[data_config["y_cols"]].to_numpy()
        self._input_dataset = tf.data.Dataset.from_tensor_slices((x, y))
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
    def dataframe(self):
        """
        The dataset dataframe.
        """
        return self._df

    @dataframe.setter
    def dataframe(self, value: pd.DataFrame):
        raise ValueError("The df property is read-only.")

    @staticmethod
    def validate_data_config(data_config: dict):
        """
        Returns true if the dictionary passed is valid.
        """
        assert {"start", "end", "x_cols", "y_cols", "detectors"}.issubset(data_config)
