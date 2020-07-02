"""Functions for saving and loading models from blob storage or local storage."""

from typing import Optional
import os
from pathlib import Path
import tensorflow as tf
from .azure.blob_storage import download_blob

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order


def save_model(
    model: gpflow.models.GPModel,
    instance_id: str,
    sas_token: Optional[str] = None,
    model_dir: Optional[str] = None,
) -> None:
    """Save a model to blob storage.

    Args:
        model: A gpflow model.
        instance_id: A unique identifier for the model.
        model_dir: A directory to store the model inside. Used as cache.
    """
    # Patrick's comment:
    # Not sure how writing to blob works from python, but I guess we need to
    # 1. create a file with the model stored inside
    # 2. copy that file to blob storage

    # NOTE I strongly recommend that we also save to file - don't want to train a model
    #       for 4 hours only to lose it due to e.g. bad internet connection

    # write to local directory
    Path(model_dir).mkdir(exist_ok=True)
    # TODO write model - should we use pickle or tensorflow/gpflow package?
    # NOTE the name of the model should be INSTANCE_ID.ext where ext is the extension

    # try saving to blob storage first
    # try:
    tf_session = model.enquire_session()
    saver_context = gpflow.saver.SaverContext(session=tf_session)
    saver = gpflow.saver.Saver()

    fp = os.path.join(model_dir, instance_id)
    saver.save(fp + ".h5", model, context=saver_context)
    tf_saver = tf.train.Saver()
    tf_saver.save(tf_session, fp)

    # except e:  # TODO what type of exception is thrown? should we catch it or just log error?



def load_model(
    instance_id: str, model_dir: Optional[str] = None, sas_token: Optional[str] = None, session = None,
) -> gpflow.models.GPModel:
    """Try to load the model from blob storage."""
    # try loading from blob storage
    # TODO what should these be set to?
    # resource_group = ""
    # storage_container_name = ""
    # blob_name = ""
    # account_url = ""
    # download_blob(
    #     resource_group,
    #     storage_container_name,
    #     blob_name,
    #     account_url,
    #     target_file,
    #     sas_token,
    # )
    filepath = os.path.join(model_dir, instance_id)
    model = gpflow.saver.Saver().load(filepath + ".h5")
    assert model.name == "helloworld"
    # tf_session = model.enquire_session()
    tf_session = session
    print("TF session:", tf_session)
    tf_saver = tf.train.Saver(allow_empty=True)
    tf_saver.restore(tf_session, filepath)
    model.compile(tf_session)
    return model
