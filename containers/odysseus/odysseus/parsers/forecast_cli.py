

import typer

app = typer.Typer()
scoot_app = typer.Typer()
app.add_typer(scoot_app)

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

