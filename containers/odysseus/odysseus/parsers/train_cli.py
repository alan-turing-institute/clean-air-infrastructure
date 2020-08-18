

import typer
from ..dates import Baseline, BaselineUpto

app = typer.Typer()
scoot_app = typer.Typer()
app.add_typer(scoot_app)

@scoot_app.command()
def gpr(
    baseline: Baseline,
) -> None:
    """Train a Gaussian Process Regression on scoot."""

@scoot_app.command()
def svgp(
    baseline: Baseline,
) -> None:
    """Train a Sparse Variational Gaussian Process on scoot."""
