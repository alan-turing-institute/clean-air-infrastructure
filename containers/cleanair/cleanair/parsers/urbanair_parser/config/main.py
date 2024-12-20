"""Configurations for urbanair."""

import shutil
import typer
from ..state import APP_DIR
from ....loggers.logcolours import red

app = typer.Typer(help="Configure CLI")


@app.command()
def path() -> None:
    """Echo the application directory."""
    typer.echo(f"{APP_DIR}")


@app.command()
def remove() -> None:
    """Delete all CLI configutation data"""

    # Create app dir
    if not APP_DIR.is_dir():
        typer.echo("Configuration does not exist")
        raise typer.Abort()

    confirm = typer.prompt(
        f"{red('You are about to delete the entire contents of the config directory.')} Would you like to continue: y/n"
    )

    if confirm == "y":
        try:
            shutil.rmtree(APP_DIR)
        except Exception as vague_exception:
            typer.echo(f"Failed to delete directory {str(APP_DIR)}")
            raise typer.Abort() from vague_exception
    else:
        raise typer.Abort()
