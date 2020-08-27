"""Functions for saving and loading models from blob storage or local storage."""

from typing import Callable, Optional
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
    save_fn: Optional[Callable[[gpflow.models.GPModel, str], None]],
    sas_token: Optional[str] = None,
    model_dir: Optional[str] = None,
    model_name: Optional[str] = "model",
) -> None:
    """Save a model to blob storage.

    Args:
        model: A gpflow model.
        instance_id: A unique identifier for the model.
        save_fn: A callable function that takes two arguments (model, filepath) and writes the model to a file.

    Keywords args:
        sas_token: SAS token for storing in blob storage.
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
    export_dir = os.path.join(model_dir, instance_id)
    Path(export_dir).mkdir(exist_ok=True, parents=True)
    logger.info("Saving model to %s", export_dir)

    # call the save function to write the model to a file
    save_fn(model, export_dir, model_name=model_name)

    # TODO try saving to blob storage - should send the whole directory
    # TODO what type of exception is thrown if blob storage fails? should we catch it or just log error?


def load_model(
    instance_id: str,
    load_fn: Callable[[str], gpflow.models.GPModel],
    compile_model: bool = True,
    model_dir: Optional[str] = None,
    model_name: str = "model",
    sas_token: Optional[str] = None,
    tf_session: Optional[tf.compat.v1.Session] = None,
) -> gpflow.models.GPModel:
    """Try to load the model from blob storage.

    Args:
        instance_id: A unique identifier for the model.
        load_fn: Loads a gpflow model from a filepath. See `cleanair.utils.tf1.load_gpflow1_model_from_file`.

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
    export_dir = os.path.join(model_dir, instance_id)

    # try loading from blob storage
    # TODO what should these be set to?
    resource_group = ""
    storage_container_name = ""
    blob_name = ""
    account_url = ""
    target_file = export_dir  # TODO check this is correct

    # TODO dump the model from blob storage to filepath (directory)
    # TODO may need to create a directory for filepath
    try:
        logger.info(
            "Loading model from blob storage and writing files locally to %s",
            export_dir,
        )
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

    # use the load function to get the model from the filepath
    model = load_fn(
        export_dir,
        compile_model=compile_model,
        model_name=model_name,
        tf_session=tf_session,
    )

    return model
