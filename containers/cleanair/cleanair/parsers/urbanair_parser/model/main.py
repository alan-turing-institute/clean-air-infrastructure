"""Parser for model fitting."""

import typer
from . import fit_cli, load_blob, model_data_cli, save_blob, setup_cli, update_cli

app = typer.Typer(help="Model fitting and data preperation")
app.add_typer(model_data_cli.app, name="data")
app.add_typer(fit_cli.app, name="fit")
app.add_typer(setup_cli.app, name="setup")
app.add_typer(save_blob.app, name="save")
app.add_typer(load_blob.app, name="load")
app.add_typer(update_cli.app, name="update")

if __name__ == "__main__":
    app()
