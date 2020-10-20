"""Generating fake data for scoot."""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import string
import random
import numpy as np
import pandas as pd
from cleanair.databases import DBWriter
from cleanair.databases.tables import ScootReading
from cleanair.mixins import ScootQueryMixin

if TYPE_CHECKING:
    from nptyping import NDArray, Int
    from cleanair.types import Borough


class ScootGenerator(ScootQueryMixin, DBWriter):
    """Read scoot queries."""

    def __init__(
        self,
        start: str,
        upto: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        detectors: Optional[str] = None,
        borough: Optional[Borough] = None,
        **kwargs
    ) -> None:
        """Initialise a synthetic scoot writer
        
        Arguments:
            start: Start datetime for fake data
            upto: generate fake data up till this datetime
            offset: Start at a different detector
            limit: At most this many detectors
            """
        self.start = start
        self.upto = upto
        self.offset = offset
        self.limit = limit
        self.detectors = detectors
        self.borough = borough
        super().__init__(**kwargs)

    def update_remote_tables(self) -> None:
        # Theres no scoot readings in the DB - lets put in some fake ones
        start = pd.date_range(self.start, self.upto, freq="H", closed="left")
        end = start + pd.DateOffset(hours=1)
        nreadings = len(start)  # number of readings for each detector

        # Detectors are already in the database as static data
        detectors = self.scoot_detectors(
            offset=self.offset,
            limit=self.limit,
            borough=self.borough,
            detectors=self.detectors,
            output_type="df",
        )["detector_id"].to_list()
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
                generate_discrete_timeseries(
                    nreadings, constant_modifier=np.random.randint(30, 300)
                )
            )
        # create a dataframe and insert the fake records
        readings = pd.DataFrame(data)
        records = readings.to_dict("records")
        self.commit_records(records, on_conflict="ignore", table=ScootReading)


def generate_discrete_timeseries(
    size: int,
    lambda_noise: int = 5,
    constant_modifier: int = 50,
    amplitude_modifier: float = 10.0,
    shift_modifier: float = 3.0,
    gradiant: float = 0.0,
) -> NDArray[Int]:
    """Create a timeseries with discrete values."""
    # set seed
    np.random.seed(0)

    X = np.linspace(0, size, num=size)

    # combine sine and cosine waves to create function
    underlying_function = (
        constant_modifier
        + gradiant * X
        + amplitude_modifier * (np.sin(0.5 * X - shift_modifier) + np.cos(X))
    )

    # floor function and add poisson noise
    return np.random.choice([-1, 1], size) * (
        np.random.poisson(lambda_noise, size) - 1
    ) + np.floor(underlying_function)


def generate_detector_id() -> str:
    """Generate a random 4 character id."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=4))


def generate_scoot_df(
    start_date: str = "2020-01-01",
    end_date: str = "2020-01-02",
    num_detectors: int = 1,
    day_of_week: int = 7,
) -> pd.DataFrame:
    """Generate a scoot dataframe.

    Args:
        start_date: First date.
        end_date: Last date (exclusive).
        num_detectors: Number of detectors to generate data for.
        day_of_week: 0 is Monday, 1 is Tuesday, etc.
            Default of 7 means all days are used.
    """
    # set seed
    random.seed(0)

    columns = [
        "detector_id",
        "measurement_start_utc",
        "measurement_end_utc",
        "n_vehicles_in_interval",
        "hour",
    ]
    scoot_df = pd.DataFrame(columns=columns)

    for _ in range(num_detectors):
        # random detector id
        detector_id = generate_detector_id()

        # new dataframe with all dates between date range
        frame = pd.DataFrame()
        frame["measurement_start_utc"] = pd.date_range(
            start=start_date, end=end_date, freq="h", closed="left"
        )
        num_observations = len(frame)

        # generate random discrete timeseries
        timeseries_center = random.randint(30, 3000)
        frame["n_vehicles_in_interval"] = generate_discrete_timeseries(
            num_observations,
            constant_modifier=timeseries_center,
            lambda_noise=int(timeseries_center / 10),
            amplitude_modifier=timeseries_center / 5,
        )
        # filter by day of week if applicable
        if day_of_week < 7:
            frame = frame.loc[
                frame["measurement_start_utc"].dt.dayofweek == day_of_week
            ]

        frame["detector_id"] = detector_id
        frame["measurement_end_utc"] = frame["measurement_start_utc"] + pd.DateOffset(
            hours=1
        )
        frame["hour"] = frame["measurement_start_utc"].dt.hour

        # append new dataframe
        assert set(scoot_df.columns) == set(frame.columns)
        scoot_df = pd.concat([scoot_df, frame], ignore_index=True, sort=False)

    return scoot_df


def create_daily_readings_df(readings: NDArray[Int]) -> pd.DataFrame:
    """Create a simple dataframe over one day for one detector."""
    random.seed(0)
    start_date = "2020-01-01"
    end_date = "2020-01-02"
    frame = pd.DataFrame()
    frame["n_vehicles_in_interval"] = readings
    frame["detector_id"] = np.repeat(generate_detector_id(), 24)
    frame["measurement_start_utc"] = pd.date_range(
        start=start_date, end=end_date, freq="h", closed="left"
    )
    frame["measurement_end_utc"] = frame["measurement_start_utc"] + pd.DateOffset(
        hours=1
    )
    frame["hour"] = frame["measurement_start_utc"].dt.hour
    return frame
