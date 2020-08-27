"""Fixtures for the file manager."""

from __future__ import annotations
from typing import TYPE_CHECKING
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from cleanair.types import Source, Species
from cleanair.parsers.urbanair_parser.file_manager import FileManager

if TYPE_CHECKING:
    from cleanair.types import TargetDict

# pylint: disable=redefined-outer-name


@pytest.fixture(scope="function")
def input_dir(tmpdir_factory) -> Path:
    """Temporary input directory."""
    return Path(tmpdir_factory.mktemp(".tmp"))


@pytest.fixture(scope="function")
def file_manager(input_dir: Path) -> FileManager:
    """A file manager rooted on the tmp directory."""
    return FileManager(input_dir=input_dir)


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
