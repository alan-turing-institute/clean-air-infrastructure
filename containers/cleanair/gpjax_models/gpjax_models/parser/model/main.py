"""Parser for JAX model fitting."""

import typer
from . import fit_cli

app = typer.Typer(help="Jax model fitting")
app.add_typer(fit_cli.app, name="fit")

if __name__ == "__main__":
    app()
