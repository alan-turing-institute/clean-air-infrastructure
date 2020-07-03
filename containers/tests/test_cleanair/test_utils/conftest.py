"""Fixtures for testing reading and writing models."""

import pytest
import tensorflow as tf


@pytest.fixture(scope="session")
def model_dir(tmpdir_factory) -> str:
    """Path to temporary model directory."""
    return tmpdir_factory.mktemp(".tmp")


@pytest.fixture(scope="function")
def model_name() -> str:
    """Name of model for testing utils."""
    return "test_model"


@pytest.fixture
def save_load_instance_id() -> str:
    """Test id for instance."""
    return "fake_instance_id"


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
