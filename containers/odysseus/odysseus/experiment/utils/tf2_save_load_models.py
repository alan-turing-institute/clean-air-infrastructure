"""Saving and loading tensorflow/gpflow 2 models.

There is an ongoing issue in tensorflow that means saving gpflow 2 models is not straighforward.

https://github.com/tensorflow/tensorflow/issues/34908

See the gpflow docs for more info (including checkpoints):
https://gpflow.readthedocs.io/en/master/notebooks/intro_to_gpflow2.html
"""

import gpflow
import tensorflow as tf

def save_gpflow2_model_to_file(model: gpflow.models.GPModel, export_dir: str, **kwargs) -> None:
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

    predict_fn = tf.function(
        frozen_model.predict_f, input_signature=[tf.TensorSpec(shape=[None, input_dim], dtype=tf.float64)]
    )
    # change the predict function
    module_to_save.predict = predict_fn

    # save the trained model to directory
    tf.saved_model.save(module_to_save, export_dir)

def load_gpflow2_model_from_file(export_dir: str, **kwargs) -> gpflow.models.GPModel:
    """Load a gpflow 2 model from file"""
    loaded_model = tf.saved_model.load(export_dir)
    return loaded_model