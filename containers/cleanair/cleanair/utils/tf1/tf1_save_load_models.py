"""Save and load gpflow1 & tensorflow 1 models."""

import os
import tensorflow as tf
from ...loggers import get_logger

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order


def save_gpflow1_model_to_file(model: gpflow.models.GPModel, export_dir: str, **kwargs) -> None:
    """Save a gpflow 1 model to a file.

    Args:
        model: A gpflow model.
        instance_id: A unique identifier for the model.
    
    Keyword args:
        model_name: A name for the model.
    """
    model_name = kwargs.pop("model_name", "model")
    filepath = os.path.join(export_dir, model_name)

    # get the tensorflow session
    tf_session = model.enquire_session()

    # save the model using gpflow
    saver_context = gpflow.saver.SaverContext(session=tf_session)
    saver = gpflow.saver.Saver()
    saver.save(filepath + ".h5", model, context=saver_context)

    # save the tensorflow session as well
    tf_saver = tf.compat.v1.train.Saver()
    tf_saver.save(tf_session, filepath)

def load_gpflow1_model_from_file(export_dir: str, **kwargs) -> gpflow.models.GPModel:
    """Load a gpflow 1 model from file.

    Args:
        export_dir: Filepath to directory for loading model.

    Keyword args:
        compile_model: If true compile the GPflow model.
        model_name: Name of the model.
        tf_session: Load the TF session into this session.

    Returns:
        Model loaded from file.
    """
    # get key word args
    compile_model: bool = kwargs.pop("compile_model", True)
    tf_session: tf.compat.v1.Session = kwargs.pop("tf_session", None)
    model_name: str = kwargs.pop("model_name", "model")

    # get filepath to model
    filepath = os.path.join(export_dir, model_name)

    logger = get_logger("Load gpflow1")

    # load the mode using gpflow
    logger.info("Loading model and tensorflow session from %s", filepath)
    model = gpflow.saver.Saver().load(filepath + ".h5")

    # create a tensorflow session if one doesn't already exist
    if tf_session is None:
        tf_session = tf.compat.v1.get_default_session()
    logger.debug("TF session: %s", tf_session)

    # load the tensorflow session
    logger.info("Restoring tensorflow session.")
    tf_saver = tf.compat.v1.train.Saver(allow_empty=True)
    tf_saver.restore(tf_session, filepath)

    # compile the model with the loaded TF session
    if compile_model:
        logger.info("Compiling loaded GP model using loaded TF session.")
        model.compile(tf_session)
    return model
