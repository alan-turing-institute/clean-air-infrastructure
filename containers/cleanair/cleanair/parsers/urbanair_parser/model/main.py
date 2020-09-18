"""Parser for model fitting."""

import typer
from . import model_data_cli, setup_cli, save_blob, load_blob

app = typer.Typer(help="Model fitting and data preperation")
app.add_typer(model_data_cli.app, name="data")
app.add_typer(setup_cli.app, name="setup")
app.add_typer(save_blob.app, name="save")
app.add_typer(load_blob.app, name="load")

if __name__ == "__main__":
    app()
