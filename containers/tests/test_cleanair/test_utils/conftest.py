"""Fixtures for testing reading and writing models."""

from pathlib import Path
import pytest
import tensorflow as tf


@pytest.fixture(scope="function")
def model_name() -> str:
    """Name of model for testing utils."""
    return "test_model"


@pytest.fixture(scope="function")
def tf_session():
    """A tensorflow session that lasts for only the scope of a function.

    Yields:
        Tensorflow session.
    """
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        yield sess


@pytest.fixture(autouse=True)
def init_graph():
    """Initialise a tensorflow graph."""
    with tf.Graph().as_default():
        yield


@pytest.fixture(scope="session")
def input_dir(tmp_path_factory) -> Path:
    """Temporary input directory."""
    return tmp_path_factory.mktemp(".tmp")
