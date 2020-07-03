"""Functions for saving and loading models from blob storage or local storage."""

from typing import Optional
import os
from pathlib import Path
import tensorflow as tf
from .azure.blob_storage import download_blob
from ..loggers import get_logger

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order


def save_model(
    model: gpflow.models.GPModel,
    instance_id: str,
    sas_token: Optional[str] = None,
    model_dir: Optional[str] = None,
    model_name: Optional[str] = "model",
) -> None:
    """Save a model to blob storage.

    Args:
        model: A gpflow model.
        instance_id: A unique identifier for the model.
        model_dir: A root directory to store the models inside.
        model_name: Name of the model.

    Notes:
        The file structure is as follows:

        model_dir/
            instance_id/
                model_name.h5       # the model itself
                checkpoint          # checkpoint for TF session
                model_name.*        # multiple files for TF sessions
    """
    logger = get_logger("Save model")
    # 1. create a directory containing the model and the TF session
    # 2. copy that directory to blob storage

    # create a local directory
    logger.info("Creating directory to save model (if it doesn't exist).")
    filepath = os.path.join(model_dir, instance_id)
    Path(filepath).mkdir(exist_ok=True)
    logger.info("Saving model to %s", filepath)
    filepath = os.path.join(filepath, model_name)

    # get the tensorflow session
    tf_session = model.enquire_session()

    # save the model using gpflow
    saver_context = gpflow.saver.SaverContext(session=tf_session)
    saver = gpflow.saver.Saver()
    saver.save(filepath + ".h5", model, context=saver_context)

    # save the tensorflow session as well
    tf_saver = tf.compat.v1.train.Saver()
    saved_path = tf_saver.save(tf_session, filepath)
    logger.info("Tensorflow session saved to %s", saved_path)

    # TODO try saving to blob storage - should send the whole directory
    # TODO what type of exception is thrown if blob storage fails? should we catch it or just log error?


def load_model(
    instance_id: str,
    compile_model: bool = True,
    model_dir: Optional[str] = None,
    model_name: str = "model",
    sas_token: Optional[str] = None,
    tf_session: Optional[tf.compat.v1.Session] = None,
) -> gpflow.models.GPModel:
    """Try to load the model from blob storage.

    Args:
        instance_id: A unique identifier for the model.

    Keyword args:
        compile_model: If true compile the GPflow model.
        model_dir: A root directory to store the models inside.
        model_name: Name of the model.
        sas_token: To load from Blob storage.
        tf_session: Load the TF session into this session.

    Returns:
        A gpflow model.
    """
    logger = get_logger("Load model")

    # filepath to dump model & session inside
    filepath = os.path.join(model_dir, instance_id)

    # try loading from blob storage
    # TODO what should these be set to?
    resource_group = ""
    storage_container_name = ""
    blob_name = ""
    account_url = ""
    target_file = filepath  # TODO check this is correct

    # TODO dump the model from blob storage to filepath (directory)
    # TODO may need to create a directory for filepath
    try:
        download_blob(
            resource_group,
            storage_container_name,
            blob_name,
            account_url,
            target_file,
            sas_token,
        )
    except Exception:
        pass  # TODO what exception should be caught?

    # load the model from the filepath
    filepath = os.path.join(filepath, model_name)

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

    if compile_model:
        logger.info("Compiling loaded GP model using loaded TF session.")
        model.compile(tf_session)
    return model
