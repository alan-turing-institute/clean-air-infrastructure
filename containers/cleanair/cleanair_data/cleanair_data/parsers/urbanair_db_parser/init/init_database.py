"""CLI for connecting to databases."""

import os
import json
from pathlib import Path
import shutil
import typer

from ..state import (
    CONFIG_SECRETFILE_PATH,
    APP_DIR,
    PROD_HOST,
    PROD_SECRET_DICT,
)
from ....loggers.logcolours import red, green
from ....databases import DBInteractor
from ..state import state

app = typer.Typer(help="Initialise the CLI to connect to a database.")


@app.command()
def local(
    secretfile: Path = typer.Option(..., help="Path to a database secret file (.json)")
) -> None:
    """Initialise the CLI to connect to a local database"""

    # Copy secretfile over
    typer.echo("Copy secretfile to urbanair config directory")
    shutil.copy(str(secretfile), str(CONFIG_SECRETFILE_PATH))


@app.command()
def docker(
    secretfile: Path = typer.Option(..., help="Path to a database secret file (.json)")
) -> None:
    DOCKER_CONFIG_SECRETFILE_PATH = Path("/root/.config/urbanair_db_cli")
    if not DOCKER_CONFIG_SECRETFILE_PATH.exists():
        DOCKER_CONFIG_SECRETFILE_PATH.mkdir(exist_ok=True, parents=False)
    """Initialise the CLI to connect to a local database"""

    # Copy secretfile over
    typer.echo("Copy secretfile to urbanair config directory")
    shutil.copy(
        str(secretfile), str(DOCKER_CONFIG_SECRETFILE_PATH / ".db_secrets.json")
    )


@app.command()
def tables():
    """Initialises DB tables from SQLAlchemy definitions"""

    state["logger"].info("Creating tables and views")

    DBInteractor(secretfile=state["secretfile"], initialise_tables=True)
