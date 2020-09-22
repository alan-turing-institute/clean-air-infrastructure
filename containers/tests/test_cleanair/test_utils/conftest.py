"""Fixtures for testing reading and writing models."""

from __future__ import annotations
from datetime import timedelta
from typing import TYPE_CHECKING
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
import tensorflow as tf
from cleanair.types import Source, Species

if TYPE_CHECKING:
    from cleanair.types import FeaturesDict, TargetDict


@pytest.fixture(scope="session")
def input_dir(tmp_path_factory) -> Path:
    """Temporary input directory."""
    return tmp_path_factory.mktemp(".tmp")
