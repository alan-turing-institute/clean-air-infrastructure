"""Class for scan stats interacting with DB."""

from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
from sqlalchemy import func
from cleanair.databases import DBWriter
from cleanair.decorators import db_query
from cleanair.mixins import ScootQueryMixin
from cleanair.timestamps import as_datetime
from ..databases.mixins import GridMixin
from ..scanstat import (
    aggregate_readings_to_grid,
    average_gridcell_scores,
    forecast,
    preprocessor,
    scan,
)


class ScanScoot(GridMixin, ScootQueryMixin, DBWriter):
    """Reading and writing scan stats for SCOOT."""

    def __init__(
        self,
        borough: str,
        forecast_hours: int,
        train_hours: int,
        upto: str,
        grid_resolution: int = 8,
        model_name: str = "HW",
        **kwargs,
    ) -> None:
        """Initialise the scan scoot class."""
        super().__init__(**kwargs)
        self.borough: str = borough
        self.forecast_hours: int = forecast_hours
        self.forecast_start: str = as_datetime(upto) - timedelta(forecast_hours)
        self.forecast_upto: str = as_datetime(upto)
        self.grid_resolution: int = grid_resolution
        self.model_name: str = model_name
        self.train_hours: int = train_hours
        self.train_start: str = as_datetime(upto) - timedelta(
            train_hours + forecast_hours
        )
        self.train_upto: str = self.forecast_start
        # load the scoot readings
        self.readings: pd.DataFrame = self.scoot_fishnet_readings(
            borough=self.borough,
            start=self.train_start,
            upto=self.train_upto,
            output_type="df",
        )

    def run(self) -> pd.DataFrame:
        """Run the scan statistics."""
        # 2) Pre-process
        processed_df = preprocessor(self.readings)
        # 3) Build Forecast
        forecast_df = forecast(
            processed_df, self.train_hours, self.forecast_hours, self.model_name
        )
        # 4) Aggregate readings/forecast to grid level
        aggregate = aggregate_readings_to_grid(forecast_df, processed_df)
        # 5) Scan
        all_scores = scan(aggregate, self.grid_resolution)
        # 6) Aggregate average scores to grid level
        grid_level_scores = average_gridcell_scores(all_scores, self.grid_resolution)
        return grid_level_scores

    @db_query
    def scoot_fishnet(self, borough: str):
        """Get a grid over a borough and join on scoot detectors.

        Args:
            borough: The name of the borough to get scoot detectors for.

        Notes:
            The geometry column of the scoot detector table is renamed to 'location'.
            The geometry column of the fishnet is 'geom'.
        """
        # TODO add xmin, ymin, xmax, ymax for each grid square
        fishnet = self.fishnet_over_borough(borough, output_type="subquery")
        detectors = self.scoot_detectors(output_type="subquery", geom_label="location")
        with self.dbcnxn.open_session() as session:
            readings = session.query(detectors, fishnet).join(
                fishnet, func.ST_Intersects(fishnet.c.geom, detectors.c.location)
            )
            return readings

    @db_query
    def scoot_fishnet_readings(
        self, borough: str, start: str, upto: Optional[str] = None,
    ):
        """Get a grid over a borough and return all scoot readings in that grid."""
        fishnet = self.scoot_fishnet(borough, output_type="subquery")
        readings = self.scoot_readings(
            start=start,
            upto=upto,
            # detectors=fishnet.c.detector_id,
            with_location=True,
            output_type="subquery",
        )
        with self.dbcnxn.open_session() as session:
            return session.query(readings).join(
                fishnet, readings.c.detector_id == fishnet.c.detector_id
            )

    def update_remote_tables(self):
        """Write the scan statistics to a database table."""
        raise NotImplementedError("Coming soon :p")
