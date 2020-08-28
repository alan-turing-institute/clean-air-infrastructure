"""Fixtures for testing reading and writing models."""

from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import tensorflow as tf
from cleanair.types import Source, Species

if TYPE_CHECKING:
    from cleanair.types import TargetDict


@pytest.fixture(scope="session")
def model_dir(tmpdir_factory) -> Path:
    """Path to temporary model directory."""
    return Path(tmpdir_factory.mktemp(".tmp"))


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

@pytest.fixture(scope="function")
def input_dir(tmpdir_factory) -> Path:
    """Temporary input directory."""
    return Path(tmpdir_factory.mktemp(".tmp"))


@pytest.fixture(scope="function")
def target_dict() -> TargetDict:
    """A fake target/result dictionary."""
    return {Source.laqn: {Species.NO2: np.ones((24, 1))}}


@pytest.fixture(scope="function")
def target_df() -> pd.DataFrame:
    """A fake target dataframe."""
    return pd.DataFrame(
        dict(
            measurement_start_utc=pd.date_range(
                "2020-01-01", "2020-01-02", freq="H", closed="left"
            ),
            NO2=np.ones(24),
            source=np.repeat(Source.laqn.value, 24),
        )
    )
