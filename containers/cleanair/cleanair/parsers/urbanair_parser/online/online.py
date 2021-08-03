import typer

from .production import app as production
from .test import app as test

app = typer.Typer(help="Online Run CLI")
app.add_typer(production, name="production")
app.add_typer(test, name="test")
