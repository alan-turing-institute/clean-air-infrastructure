"""AQE input CLI"""
from datetime import datetime, timedelta
import typer
from cleanair.processors import ScootPerDetectorForecaster
from ..shared_args import (
    UpTo,
    NDays,
    NDays_callback,
    UpTo_callback,
    NHours,
    ScootDetectors,
)
from ..state import state
from ....timestamps import as_datetime

app = typer.Typer()


@app.command()
def check(upto: str = UpTo, nhours: int = NHours, ndays: int = NDays) -> None:
    """Check what SCOOT forecasts are in the database"""
    typer.echo("Not yet implemented")
    typer.echo(f"Options provided: upto: {upto}; nhours {nhours}; ndays {ndays}")


@app.command()
def forecast(
    trainupto: str = typer.Option(
        "today", callback=UpTo_callback, help="Up to what datetime to train the model",
    ),
    traindays: int = typer.Option(
        2, callback=NDays_callback, help="Number of days to train on", show_default=True
    ),
    trainhours: int = typer.Option(
        0, help="Number of hours to train on. Added to traindays", show_default=True
    ),
    preddays: int = typer.Option(
        2,
        callback=NDays_callback,
        help="Number of days to predict for",
        show_default=True,
    ),
    predhours: int = typer.Option(
        0, help="Number of hours to predict on. Added to preddays", show_default=True
    ),
    detectors: str = ScootDetectors,
) -> None:
    """Use SCOOT readings to generate forecasts into the future"""

    typer.echo("Forecasting SCOOT readings")

    # Train using data from the (trainhours + traindays) hours before trainupto
    # Forecast over the training range plus an additional (preddays + predhours) hours
    training_end_time = min(
        datetime.now().replace(second=0, microsecond=0, minute=0),
        as_datetime(trainupto),
    )
    forecast_start_time = training_end_time - timedelta(hours=trainhours + traindays)
    forecast_length_hrs = preddays + predhours + traindays + trainhours

    # Fit SCOOT readings using Prophet and forecast into the future
    scoot_forecaster = ScootPerDetectorForecaster(
        nhours=traindays + trainhours,  # note that this is auto-converted to hours
        end=training_end_time,
        forecast_start_time=forecast_start_time,
        forecast_length_hrs=forecast_length_hrs,
        detector_ids=detectors if detectors else None,
        secretfile=state["secretfile"],
    )
    scoot_forecaster.update_remote_tables()
