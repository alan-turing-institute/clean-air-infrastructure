

import typer

app = typer.Typer()
scoot_app = typer.Typer()
app.add_typer(scoot_app)

@scoot_app.command()
def gpr() -> None:
    """Train a Gaussian Process Regression on scoot."""