"""Fixtures for the file manager."""

from pathlib import Path
import pytest
from cleanair.parsers.urbanair_parser.file_manager import FileManager

#pylint: disable=redefined-outer-name

@pytest.fixture(scope="function")
def input_dir(tmpdir_factory) -> Path:
    """Temporary input directory."""
    return Path(tmpdir_factory.mktemp(".tmp"))

@pytest.fixture(scope="function")
def file_manager(input_dir: Path) -> FileManager:
    """A file manager rooted on the tmp directory."""
    return FileManager(input_dir=input_dir)
