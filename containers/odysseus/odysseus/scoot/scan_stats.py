"""Class for scan stats interacting with DB."""

from datetime import timedelta
from typing import Optional
import pandas as pd
from sqlalchemy import func, inspect
from cleanair.databases import DBWriter
from cleanair.databases.tables.scan_tables import FishnetTable, ScootScanStats
from cleanair.decorators import db_query
from cleanair.loggers import get_logger
from cleanair.mixins import ScootQueryMixin
from cleanair.timestamps import as_datetime
from ..databases.mixins import GridMixin
from ..scanstat import (
    preprocessor,
    intersect_processed_data,
    aggregate_readings_to_grid,
    forecast,
    scan,
    average_gridcell_scores,
)
from ..types import Borough


class ScanScoot(GridMixin, ScootQueryMixin, DBWriter):
    """Reading and writing scan stats for SCOOT."""

    def __init__(
        self,
        borough: Borough,
        forecast_hours: int,
        forecast_upto: str,
        train_hours: int,
        train_upto: str,
        grid_resolution: int = 8,
        model_name: str = "HW",
        **kwargs,
    ) -> None:
        """Initialise the scan scoot class."""
        super().__init__(**kwargs)
        self.borough: Borough = borough
        self.forecast_hours: int = forecast_hours
        self.forecast_days: int = int(forecast_hours / 24)
        self.forecast_start: str = as_datetime(forecast_upto) - timedelta(
            hours=forecast_hours
        )
        self.forecast_upto: str = as_datetime(forecast_upto)
        self.grid_resolution: int = grid_resolution
        self.logger = get_logger("scan_scoot")
        self.model_name: str = model_name
        self.train_hours: int = train_hours
        self.train_days: int = int(train_hours / 24)
        self.train_start: str = as_datetime(train_upto) - timedelta(hours=train_hours)
        self.train_upto: str = as_datetime(train_upto)
        # load the scoot readings with the fishnet joined on
        self.logger.info("Getting scoot readings and fishnet from the database.")

        # separated train and forecast timeperiods so we must also separate their dataframes.
        self.training_readings: pd.DataFrame = self.scoot_fishnet_readings(
            start=self.train_start, upto=self.train_upto, output_type="df",
        )
        self.test_readings: pd.DataFrame = self.scoot_fishnet_readings(
            start=self.forecast_start, upto=self.forecast_upto, output_type="df",
        )
        # if no readings are returned then raise a value error
        error_message = (
            "No scoot readings were returned from the DB for {period} period. "
        )
        error_message += (
            "This could be because there is no scoot data in the time range "
        )
        error_message += "or because the fishnet does not exist in the database."
        if len(self.training_readings) == 0:
            raise ValueError(error_message.format(period="training"))
        if len(self.test_readings) == 0:
            raise ValueError(error_message.format(period="forecasting"))
        self.scores_df: pd.DataFrame = None  # assigned in run() method

    def run(self) -> pd.DataFrame:
        """Run the scan statistics."""

        # 1) Pre-process both training and test data
        processed_train = preprocessor(self.training_readings, readings_type="train")
        processed_test = preprocessor(self.test_readings, readings_type="test")

        # 2) Make sure that both of the above dataframes span the same detector set
        processed_train, processed_test = intersect_processed_data(
            processed_train, processed_test
        )

        # 3) Build Forecast
        forecast_df = forecast(
            processed_train,
            processed_test,
            self.train_start,
            self.train_upto,
            self.forecast_start,
            self.forecast_upto,
            self.model_name,
        )

        # 4) Aggregate forecast dataframe to grid level. Less to search through in scan
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
        # Return dataframe to be stored in database
        return grid_level_scores

    @db_query
    def scoot_fishnet(self):
        """Get a grid over a borough and join on scoot detectors.

        Notes:
            The geometry column of the scoot detector table is renamed to 'location'.
            The geometry column of the fishnet is 'geom'.
        """
        fishnet = self.fishnet_query(
            self.borough, self.grid_resolution, output_type="subquery"
        )
        detectors = self.scoot_detectors(output_type="subquery", geom_label="location")
        with self.dbcnxn.open_session() as session:
            readings = session.query(detectors, fishnet).join(
                fishnet, func.ST_Intersects(fishnet.c.geom, detectors.c.location)
            )
            return readings

    @db_query
    def scoot_fishnet_readings(
        self, start: str, upto: Optional[str] = None,
    ):
        """Get a grid over a borough and return all scoot readings in that grid."""
        fishnet = self.scoot_fishnet(output_type="subquery")
        readings = self.scoot_readings(
            start=start, upto=upto, with_location=False, output_type="subquery",
        )
        with self.dbcnxn.open_session() as session:
            # Yields df with duplicate columns
            return session.query(
                readings,
                fishnet.c.lon,
                fishnet.c.lat,
                fishnet.c.location,
                fishnet.c.point_id,  # point id of fishnet grid square, not detector
                fishnet.c.grid_resolution,
                fishnet.c.row,
                fishnet.c.col,
                fishnet.c.geom,
            ).join(fishnet, fishnet.c.detector_id == readings.c.detector_id,)

    def update_remote_tables(self) -> None:
        """Write the scan statistics to a database table."""
        # Need to attach the point_id to scores_df
        # Only way to get all grid_res ** 2 point id's is to call fishnet_query
        fishnet_df = self.fishnet_query(
            self.borough, self.grid_resolution, output_type="df"
        )
        final_scores_df = self.scores_df.merge(
            fishnet_df[["row", "col", "point_id"]], on=["row", "col"], how="left",
        )
        # create records for the scores
        scores_inst = inspect(ScootScanStats)
        scores_cols = [c_attr.key for c_attr in scores_inst.mapper.column_attrs]
        scores_records = final_scores_df[scores_cols].to_dict("records")
        self.commit_records(
            scores_records, table=ScootScanStats, on_conflict="overwrite"
        )


class Fishnet(GridMixin, DBWriter):
    """Create and load fishnets over boroughs."""

    def __init__(self, borough: Borough, grid_resolution: int, **kwargs):
        """Initialise the fishnet."""
        super().__init__(**kwargs)
        self.borough: Borough = borough
        self.grid_resolution: int = grid_resolution

    def update_remote_tables(self) -> None:
        """Update the scoot fishnet tables using the fishnet_df dataframe."""
        # create the fishnet over the borough
        fishnet_df: pd.DataFrame = self.fishnet_over_borough(
            borough=self.borough, grid_resolution=self.grid_resolution, output_type="df"
        )
        # add the borough column
        fishnet_df["borough"] = self.borough.value
        fishnet_df["grid_resolution"] = self.grid_resolution

        # create records for the fishnet
        fishnet_inst = inspect(FishnetTable)
        fishnet_cols = [c_attr.key for c_attr in fishnet_inst.mapper.column_attrs]
        fishnet_cols.remove("point_id")  # will be created automatically on DB

        fishnet_records = fishnet_df[fishnet_cols].to_dict("records")
        self.commit_records(fishnet_records, table=FishnetTable, on_conflict="ignore")
