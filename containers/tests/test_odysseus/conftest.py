"""Fixtures for odysseus module."""

import pytest
from ..data_generators.scoot_generator import generate_scoot_df


@pytest.fixture(scope="function")
def scoot_df():
    """Fake dataframe of realistic scoot data."""
    return generate_scoot_df(end_date="2020-01-03", num_detectors=2)
