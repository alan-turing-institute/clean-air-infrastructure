"""Parser for model vis."""

import typer
from . import vis

app = typer.Typer(help="Jax model visualization")
app.add_typer(vis.app, name="vis")

if __name__ == "__main__":
    app()
