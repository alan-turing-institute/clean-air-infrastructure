"""CLI for scan stats."""

import typer
from cleanair.loggers import get_logger
from cleanair.parsers.urbanair_parser.shared_args import (
    NDays,
    NHours,
    UpTo,
)
from cleanair.parsers.urbanair_parser.state import state
from .shared_args import Borough, GridResolution, ModelName
from ..scoot import Fishnet, ScanScoot

app = typer.Typer()


@app.command()
def scoot(
    borough: str = Borough,
    grid_resolution: int = GridResolution,
    forecast_days: int = NDays,
    forecast_hours: int = NHours,
    forecast_upto: str = UpTo,
    model_name: str = ModelName,
    train_days: int = NDays,
    train_hours: int = NHours,
    train_upto: str = UpTo,
) -> None:
    """Run scan stats on scoot."""
    logger = get_logger("scan_scoot")
    secretfile: str = state["secretfile"]
    # NOTE days converted to hours with ndays callback
    train_hours = train_days + train_hours
    forecast_hours = forecast_days + forecast_hours

    # run the scan stats
    scan_scoot = ScanScoot(
        borough=borough,
        forecast_hours=forecast_hours,
        forecast_upto=forecast_upto,
        train_hours=train_hours,
        train_upto=train_upto,
        grid_resolution=grid_resolution,
        model_name=model_name,
        secretfile=secretfile,
    )
    scan_df = scan_scoot.run()
    logger.debug("Columns: %s", list(scan_df.columns))
    logger.debug(scan_df.sample(10))
    scan_scoot.update_remote_tables()


@app.command()
def setup(borough: str = Borough, grid_resolution: int = GridResolution,) -> None:
    """Create a fishnet over a borough with the given grid resolution."""
    fishnet = Fishnet(borough, grid_resolution, secretfile=state["secretfile"])
    fishnet.update_remote_tables()
