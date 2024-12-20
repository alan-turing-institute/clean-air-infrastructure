"""Fixtures for testing reading and writing models."""

from __future__ import annotations
from datetime import timedelta
from typing import List, TYPE_CHECKING
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from cleanair.types import ModelName, Source, Species
from cleanair.utils.file_manager import FileManager

if TYPE_CHECKING:
    from cleanair.types import FeaturesDict, TargetDict

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="function")
def model_name() -> ModelName:
    """Name of model for testing utils."""
    return ModelName.svgp


@pytest.fixture(scope="session")
def input_dir(tmp_path_factory) -> Path:
    """Temporary input directory."""
    return tmp_path_factory.mktemp(".tmp")


@pytest.fixture(scope="function")
def file_manager(input_dir) -> FileManager:
    """Fixture for file manager."""
    return FileManager(input_dir)


@pytest.fixture(scope="function")
def dataset_dict(dataset_start_date, dataset_end_date) -> FeaturesDict:
    """A fake X and Y wrapped up in a dataframe for a single source (laqn)."""
    days = 2
    return {
        Source.laqn: pd.DataFrame(
            dict(
                measurement_start_utc=pd.date_range(
                    dataset_start_date,
                    dataset_end_date - timedelta(days=days),
                    freq="H",
                    closed="left",
                ),
                lon=np.random.rand(days * 24),
                lat=np.random.rand(days * 24),
                no2=np.random.rand(days * 24),
            )
        )
    }


@pytest.fixture(scope="function")
def target_dict() -> TargetDict:
    """A fake target/result dictionary."""
    return {Source.laqn: {Species.NO2: np.ones((24, 1))}}


@pytest.fixture(scope="function")
def target_df(dataset_start_date, dataset_end_date) -> pd.DataFrame:
    """A fake target dataframe."""
    days = 2
    return pd.DataFrame(
        dict(
            measurement_start_utc=pd.date_range(
                dataset_start_date + timedelta(days=days),
                dataset_end_date,
                freq="H",
                closed="left",
            ),
            NO2=np.ones(days * 24),
            source=np.repeat(Source.laqn.value, days * 24),
        )
    )


@pytest.fixture(scope="function")
def elbo() -> List[float]:
    """ELBO observations"""
    return [1.0] * 10
