"""Fixtures for odysseus module."""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional
import pytest
import numpy as np
import pandas as pd
from .data_generators import generate_discrete_timeseries, generate_scoot_df
from cleanair.databases import DBWriter
from cleanair.databases.tables import ScootReading
from cleanair.decorators import db_query
from cleanair.mixins import ScootQueryMixin

if TYPE_CHECKING:
    from cleanair.databases import Connector

@pytest.fixture(scope="function")
def scoot_start() -> str:
    """Start date of scoot readings."""
    return "2020-01-01"

@pytest.fixture(scope="function")
def scoot_upto() -> str:
    """Upto date of scoot readings."""
    return "2020-01-31"

@pytest.fixture(scope="function")
def scoot_offset() -> int:
    """Get detectors starting at this index in the detector table."""
    return 0

@pytest.fixture(scope="function")
def scoot_limit() -> int:
    """Limit the number of detectors to this number."""
    return 1000

@pytest.fixture(scope="function")
def scoot_df() -> pd.DataFrame:
    """Fake dataframe of realistic scoot data."""
    return generate_scoot_df(end_date="2020-01-03", num_detectors=2)

class ScootWriter(ScootQueryMixin, DBWriter):
    """Read scoot queries."""

    def __init__(self, start: str, upto: str, offset: int, limit: int, **kwargs):
        """Initialise a synthetic scoot writer."""
        self.start = start
        self.upto = upto
        self.offset = offset
        self.limit = limit
        super().__init__(**kwargs)

    def update_remote_tables(self) -> None:
        # Theres no scoot readings in the DB - lets put in some fake ones
        start = pd.date_range(self.start, self.upto, freq="H", closed="left")
        end = start + pd.DateOffset(hours=1)
        nreadings = len(start)  # number of readings for each detector
        detectors = self.scoot_detectors(offset=self.offset, limit=self.limit, output_type="df")["detector_id"].to_list()
        nrows = nreadings * len(detectors)

        data = dict(
            detector_id=list(),
            measurement_start_utc=list(),
            measurement_end_utc=list(),
            n_vehicles_in_interval=list(),
            occupancy_percentage=np.zeros(nrows),
            congestion_percentage=np.zeros(nrows),
            saturation_percentage=np.zeros(nrows),
            flow_raw_count=np.zeros(nrows),
            occupancy_raw_count=np.zeros(nrows),
            congestion_raw_count=np.zeros(nrows),
            saturation_raw_count=np.zeros(nrows),
            region=np.repeat("None", nrows),
        )
        for d in detectors:
            data["detector_id"].extend([d] * nreadings)
            data["measurement_start_utc"].extend(list(start))
            data["measurement_end_utc"].extend(list(end))
            data["n_vehicles_in_interval"].extend(
                generate_discrete_timeseries(nreadings, constant_modifier=np.random.randint(30, 300))
            )
        # create a dataframe and insert the fake records
        readings = pd.DataFrame(data)
        records = readings.to_dict("records")
        self.commit_records(records, on_conflict="ignore", table=ScootReading)

@pytest.fixture(scope="function")
def scoot_writer(
    secretfile: str,
    connection: Connector,
    scoot_start: str,
    scoot_upto: str,
    scoot_offset: int,
    scoot_limit: int,
) -> ScootWriter:
    """Initialise a scoot writer."""
    return ScootWriter(scoot_start, scoot_upto, scoot_offset, scoot_limit, secretfile=secretfile, connection=connection)
