"""CLI for connecting to databases."""

import subprocess
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

    try:
        user_cmd = subprocess.run(
            ["az", "ad", "signed-in-user", "show", "-o", "json"],
            capture_output=True,
            check=True,
        )

        username = json.loads(user_cmd.stdout.decode())["userPrincipalName"]

    except Exception:
        typer.echo("Could not get active user. Have you run 'az login'")
        raise typer.Abort()

    # Create app dir
    if not os.path.isdir(APP_DIR):
        os.mkdir(APP_DIR)

    # Request an access token
    typer.echo(
        f"Requesting access token for {green(username)} to connect to {green(PROD_HOST)}"
    )

    try:
        token_cmd = subprocess.run(
            [
                "az",
                "account",
                "get-access-token",
                "--resource-type",
                "oss-rdbms",
                "--query",
                "accessToken",
                "-o",
                "tsv",
            ],
            check=True,
            capture_output=True,
        )
    except:
        typer.echo(
            f"Failed to get an access token for {green(username)}. Do you have DB access?"
        )
        raise typer.Abort()

    token = token_cmd.stdout.decode("utf-8")[:-1]

    PROD_SECRET_DICT["password"] = token
    PROD_SECRET_DICT["username"] = username + "@cleanair-inputs-server"

    # Create config secretfile
    with open(CONFIG_SECRETFILE_PATH, "w") as secretfile:
        json.dump(PROD_SECRET_DICT, secretfile, indent=4)

    typer.echo(
        f"Credentials for {green(username)} writen to {CONFIG_SECRETFILE_PATH}\n"
        f"To remove credentials call {green('urbanair remove_config')}\n"
        f"{red('Credentials will expire after 5-60 minutes.')} If access required for longer contact admin"
    )
