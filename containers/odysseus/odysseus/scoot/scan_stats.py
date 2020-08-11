"""Class for scan stats interacting with DB."""

from datetime import timedelta
from typing import Any, Optional
import pandas as pd
from sqlalchemy import func, inspect
from cleanair.databases import DBWriter
from cleanair.databases.tables.scan_tables import Fishnet, ScootScanStats
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
        self.forecast_days: int = int(forecast_hours / 24)
        self.forecast_start: str = as_datetime(upto) - timedelta(hours=forecast_hours)
        self.forecast_upto: str = as_datetime(upto)
        self.grid_resolution: int = grid_resolution
        self.model_name: str = model_name
        self.train_hours: int = train_hours
        self.train_days: int = int(train_hours / 24)
        self.train_start: str = as_datetime(upto) - timedelta(
            hours=train_hours + forecast_hours
        )
        self.train_upto: str = self.forecast_start
        self.fishnet_df: pd.DataFrame = self.fishnet_over_borough(
            borough=self.borough, grid_resolution=self.grid_resolution, output_type="df"
        )
        # load the scoot readings
        self.readings: pd.DataFrame = self.scoot_fishnet_readings(
            borough=self.borough,
            start=self.train_start,
            upto=self.forecast_upto,
            output_type="df",
        )
        self.scores_df: pd.DataFrame = None  # assigned in run() method

    def run(self) -> pd.DataFrame:
        """Run the scan statistics."""
        # 2) Pre-process
        processed_df = preprocessor(self.readings)
        # 3) Build Forecast
        forecast_df = forecast(
            processed_df,
            self.train_start,
            self.train_upto,
            self.forecast_start,
            self.forecast_upto,
            self.model_name,
        )
        # 4) Aggregate readings/forecast to grid level
        aggregate = aggregate_readings_to_grid(forecast_df)
        # 5) Scan
        all_scores = scan(
            aggregate, self.grid_resolution, self.forecast_start, self.forecast_upto
        )
        # 6) Aggregate average scores to grid level
        grid_level_scores = average_gridcell_scores(
            all_scores, self.grid_resolution, self.forecast_start, self.forecast_upto
        )
        self.scores_df = grid_level_scores
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
        fishnet = self.fishnet_over_borough(
            borough, self.grid_resolution, output_type="subquery"
        )
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
            with_location=False,
            output_type="subquery",
        )
        with self.dbcnxn.open_session() as session:
            # Yields df with duplicate columns
            return session.query(
                readings,
                fishnet.c.lon,
                fishnet.c.lat,
                fishnet.c.location,
                fishnet.c.row,
                fishnet.c.col,
                fishnet.c.geom,
            ).join(fishnet, fishnet.c.detector_id == readings.c.detector_id,)

    @db_query
    def fishnet_query(self, borough: str) -> Any:
        """Query the Fishnet table.

        Args:
            borough: Name of the borough to get the fishnet for.

        Returns:
            A database query.
        """
        with self.dbcnxn.open_session() as session:
            fishnet_with_points = session.query(Fishnet).filter(
                Fishnet.borough == self.borough
            )
            return fishnet_with_points

    def update_remote_tables(self) -> None:
        """Write the scan statistics to a database table."""
        # TODO code written badly in a rush - will almost certainly break
        # create records for the fishnet
        # TODO in future pushing the fishnet to DB should be a separate function
        fishnet_inst = inspect(Fishnet)
        fishnet_cols = [c_attr.key for c_attr in fishnet_inst.mapper.column_attrs]
        fishnet_records = self.fishnet_df[fishnet_cols].to_dict("records")

        # need to commit records for the fishnet before scores
        self.commit_records(fishnet_records, table=Fishnet, on_conflict="overwrite")

        # get the point id, row and columns
        fishnet_with_points: pd.DataFrame = self.fishnet_query(
            self.borough, output_type="df"
        )

        # TODO snap a point_id column from fishnet_with_points onto the self.scores_df by joining on row & col

        # create records for the scores
        scores_inst = inspect(ScootScanStats)
        scores_cols = [c_attr.key for c_attr in scores_inst.mapper.column_attrs]
        scores_records = self.scores_df[scores_cols].to_dict("records")
        self.commit_records(scores_records, table=ScootScanStats, on_conflict="ignore")
