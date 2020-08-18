"""CLI for scan stats."""

from datetime import timedelta
import typer
from cleanair.loggers import get_logger
from cleanair.parsers.urbanair_parser.shared_args import (
    NDays,
    NHours,
    UpTo,
)
from cleanair.parsers.urbanair_parser.state import state
from cleanair.timestamps import as_datetime
from ..dates import Baseline, BaselineUpto
from .shared_args import Borough, GridResolution, ModelName
from ..scoot import Fishnet, ScanScoot

app = typer.Typer()


@app.command()
def scoot(
    baseline: Baseline,
    borough: str = Borough,
    grid_resolution: int = GridResolution,
    forecast_days: int = NDays,
    forecast_hours: int = NHours,
    forecast_upto: str = UpTo,
    model_name: str = ModelName,
    # train_days: int = NDays,
    # train_hours: int = NHours,
    # train_upto: str = UpTo,
) -> None:
    """Run scan stats on scoot."""
    logger = get_logger("scan_scoot")
    secretfile: str = state["secretfile"]

    # NOTE days converted to hours with ndays callback
    forecast_hours = forecast_days + forecast_hours

    train_hours = 21 * 24
    # if baseline == Baseline.custom:
    #     train_hours = train_days + train_hours

    if baseline == Baseline.last3weeks:
        train_upto = (as_datetime(forecast_upto) - timedelta(hours=forecast_hours)).isoformat()
    else:
        train_upto: str = BaselineUpto[baseline.value].value

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
