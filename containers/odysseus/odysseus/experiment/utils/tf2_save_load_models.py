"""Saving and loading tensorflow/gpflow 2 models.

There is an ongoing issue in tensorflow that means saving gpflow 2 models is not straighforward.

https://github.com/tensorflow/tensorflow/issues/34908

See the gpflow docs for more info (including checkpoints):
https://gpflow.readthedocs.io/en/master/notebooks/intro_to_gpflow2.html
"""

from typing import Union
import gpflow
import tensorflow as tf


def save_gpflow2_model_to_file(
    model: gpflow.models.GPModel, export_dir: str, **kwargs
) -> None:
    """Save a gpflow 2 model to file.

    Args:
        model: Model to save.
        export_dir: Filepath to the directory to store the model.

    Keywords args:
        input_dim: Number of dimensions of the input tensor.
    """
    # NOTE the input dim needs to be changed for input tensors of different dimensions
    input_dim: int = kwargs.pop("input_dim", 1)

    # we need to freeze the model due to the issue above
    frozen_model = gpflow.utilities.freeze(model)

    module_to_save = tf.Module()

    # save the predict_f_samples function which also take an integer
    module_to_save.predict_f_samples = tf.function(
        frozen_model.predict_f_samples,
        input_signature=[tf.TensorSpec(shape=[None, input_dim], dtype=tf.float64), tf.TensorSpec(shape=None, dtype=tf.int64)],
    )
    # save the predict_f function
    module_to_save.predict_f = tf.function(
        frozen_model.predict_f_samples,
        input_signature=[tf.TensorSpec(shape=[None, input_dim], dtype=tf.float64)],
    )

    # save the trained model to directory
    tf.saved_model.save(module_to_save, export_dir)


def load_gpflow2_model_from_file(
    export_dir: str, **kwargs
) -> Union[gpflow.models.GPModel, None]:
    """Load a gpflow 2 model from file.

    Args:
        export_dir: Directory to load model from.

    Returns:
        A model if the directory exists, otherwise None.
    """
    try:
        loaded_model = tf.saved_model.load(export_dir)
        return loaded_model

    except OSError:
        tf.get_logger().error("Model failed to load from directory %s", export_dir)
        return None
