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
from cleanair.types import Borough
from ..dates import Baseline, BaselineUpto
from .shared_args import BoroughOption, GridResolution, ModelName
from ..scoot import Fishnet, ScanScoot

app = typer.Typer(
    help="Run scan statistics for scoot against a given training baseline period."
)


@app.command()
def scoot(
    baseline: Baseline,
    borough: Borough = BoroughOption,
    grid_resolution: int = GridResolution,
    forecast_days: int = NDays,
    forecast_hours: int = NHours,
    forecast_upto: str = UpTo,
    model_name: str = ModelName,
) -> None:
    """Run scan stats on scoot."""
    logger = get_logger("scan_scoot")
    secretfile: str = state["secretfile"]

    # NOTE days converted to hours with ndays callback
    forecast_hours = forecast_days + forecast_hours
    train_hours = 21 * 24  # 3 weeks

    if baseline == Baseline.last3weeks:
        train_upto = (
            as_datetime(forecast_upto) - timedelta(hours=forecast_hours)
        ).isoformat()
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
def setup(
    borough: Borough = Borough.westminster, grid_resolution: int = GridResolution,
) -> None:
    """Create a fishnet over a borough with the given grid resolution."""
    fishnet = Fishnet(borough, grid_resolution, secretfile=state["secretfile"])
    fishnet.update_remote_tables()
