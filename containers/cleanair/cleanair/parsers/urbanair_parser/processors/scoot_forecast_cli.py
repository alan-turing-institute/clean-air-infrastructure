"""AQE input CLI"""
from datetime import datetime  # , timedelta
import typer
from ....processors import ScootPerDetectorForecaster
from ..shared_args import From, UpTo, NDays, NDays_callback, NHours, ScootDetectors
from ..state import state
from ....timestamps import as_datetime

app = typer.Typer()

ModelDays = typer.Option(  # pylint: disable=invalid-name
    14,
    help="Number of days to use for building the forecast model",
    show_default=True,
    callback=NDays_callback,
)


@app.command()
def check(upto: str = UpTo, nhours: int = NHours, ndays: int = NDays) -> None:
    """Check what SCOOT forecasts are in the database"""
    typer.echo("Not yet implemented")
    typer.echo(f"Options provided: upto: {upto}; nhours {nhours}; ndays {ndays}")


@app.command()
def forecast(
    fromdate: str = From,
    nhours: int = NHours,
    ndays: int = NDays,
    modeldays: int = ModelDays,
    detectors: str = ScootDetectors,
) -> None:
    """Use SCOOT readings to generate forecasts into the future"""

    typer.echo("Forecasting SCOOT readings")

    # Set time parameters
    forecast_length_hrs = nhours + ndays  # note that this is auto-converted to hours
    forecast_start_time = as_datetime(fromdate)
    model_data_end_time = min(datetime.now(), forecast_start_time).replace(
        second=0, microsecond=0, minute=0
    )

    # Fit SCOOT readings using Prophet and forecast into the future
    scoot_forecaster = ScootPerDetectorForecaster(
        nhours=modeldays,  # note that this is auto-converted to hours
        end=model_data_end_time,
        forecast_start_time=forecast_start_time,
        forecast_length_hrs=forecast_length_hrs,
        detector_ids=detectors if detectors else None,
        secretfile=state["secretfile"],
    )
    scoot_forecaster.update_remote_tables()