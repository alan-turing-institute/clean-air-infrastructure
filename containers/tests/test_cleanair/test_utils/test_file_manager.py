"""Tests for saving and loading files for an air quality model."""

from __future__ import annotations
from typing import TYPE_CHECKING
import os
import numpy as np
import tensorflow as tf
import pandas as pd
from cleanair.types import Source
from cleanair.utils import FileManager

# turn off tensorflow warnings for gpflow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
import gpflow  # pylint: disable=wrong-import-position,wrong-import-order

if TYPE_CHECKING:
    from pathlib import Path
    from cleanair.types import (
        DataConfig,
        FeaturesDict,
        TargetDict,
    )


def test_save_load_data_config(input_dir: Path, valid_config: DataConfig) -> None:
    """Test data config is saved and loaded correctly."""
    file_manager = FileManager(input_dir)
    # save data config to file
    file_manager.save_data_config(valid_config, full=False)
    assert (file_manager.input_dir / FileManager.DATA_CONFIG).exists()

    # load data config from file
    loaded_config = file_manager.load_data_config(full=False)
    for key, value in valid_config:
        assert hasattr(loaded_config, key)
        assert value == getattr(loaded_config, key)
