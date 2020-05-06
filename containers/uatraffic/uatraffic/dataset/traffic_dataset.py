"""
A traffic dataset.
"""

import tensorflow as tf
from cleanair.databases import DBReader
from cleanair.mixins import ScootQueryMixin
from ..preprocess.normalise import normalise_datetime

class TrafficDataset(DBReader, ScootQueryMixin, tf.data.Dataset):
    """
    A traffic dataset that queries the database given a data config dictionary.
    """

    def __init__(self, data_config: dict, secretfile: str, **kwargs):
        # check the data config dictionary is valid
        TrafficDataset.validate_data_config(data_config)

        # load a database reader super class
        DBReader.__init__(self, secretfile=secretfile, **kwargs)

        # store the data config - access with property
        self._data_config = data_config

        # load scoot from the data config
        # TODO: add day of week
        self._df = self.get_scoot_with_location(
            self._data_config["start"],
            end_time=self._data_config["end"],
            detectors=self._data_config["detectors"],
            output_type="df",
        )
        # normalise datetime
        self._df = normalise_datetime(self._df)

        # create numpy arrays of the x and y columns
        x = self._df[data_config["x_cols"]].to_numpy()
        y = self._df[data_config["y_cols"]].to_numpy()

        # load the dataset from the numpy arrays
        dataset = tf.data.Dataset.from_tensor_slices((x, y))

        # cast to float 64
        self._input_dataset = dataset.map(
            lambda x, y: (tf.cast(x, tf.float64), tf.cast(y, tf.float64))
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
    def dataframe(self):
        """The dataset dataframe."""
        return self._df

    @property
    def features(self):
        """The features tensor."""
        return tf.stack([element[0] for element in self._input_dataset])

    @property
    def target(self):
        """The target tensor."""
        return tf.stack([element[1] for element in self._input_dataset])

    @staticmethod
    def validate_data_config(data_config: dict):
        """
        Returns true if the dictionary passed is valid.
        """
        assert {"start", "end", "x_cols", "y_cols", "detectors", "weekdays"}.issubset(data_config)
