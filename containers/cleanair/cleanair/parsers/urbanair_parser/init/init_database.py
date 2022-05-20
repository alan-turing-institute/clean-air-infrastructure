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
from ....utils.database_authentication import (
    get_database_access_token,
    get_database_username,
)

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
def production() -> None:
    """Initialise the CLI to connect to the production database

    Ensure you have run 'az login' first"""

    # Create app dir
    if not os.path.isdir(APP_DIR):
        os.mkdir(APP_DIR)

    username = get_database_username()

    # Request an access token
    typer.echo(
        f"Requesting access token for {green(username)} to connect to {green(PROD_HOST)}"
    )

    PROD_SECRET_DICT["password"] = get_database_access_token()
    PROD_SECRET_DICT["username"] = username

    # Create config secretfile
    with open(CONFIG_SECRETFILE_PATH, "w") as secretfile:
        json.dump(PROD_SECRET_DICT, secretfile, indent=4)

    typer.echo(
        f"Credentials for {green(username)} written to {CONFIG_SECRETFILE_PATH}\n"
        f"To remove credentials call {green('urbanair remove_config')}\n"
        f"{red('Credentials will expire after 5-60 minutes.')} If access required for longer contact admin"
    )


@app.command()
def tables():
    """Initialises DB tables from SQLAlchemy definitions"""

    state["logger"].info("Creating tables and views")

    DBInteractor(secretfile=state["secretfile"], initialise_tables=True)
