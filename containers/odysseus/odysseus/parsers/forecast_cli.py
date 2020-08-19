

import typer
from cleanair.parsers.urbanair_parser.shared_args import NDays, NHours, UpTo


app = typer.Typer(help="Forecasting for Odysseus.")
scoot_app = typer.Typer(help="Scoot forecasting.")
app.add_typer(scoot_app, name="scoot")

@scoot_app.command()
def gpr() -> None:
    """Forecast a Gaussian Process Regression model on scoot."""
    raise NotImplementedError()

@scoot_app.command()
def svgp(
    forecast_days: int = NDays,
    forecast_hours: int = NHours,
    forecast_upto: str = UpTo,
) -> None:
    """Forecast an SVGP."""
