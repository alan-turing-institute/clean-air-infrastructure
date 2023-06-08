"""Commands for echoing useful information"""

import typer
from ....utils.database_authentication import (
    get_database_access_token,
    get_database_username,
)

app = typer.Typer(help="Echo useful information to stdout")


@app.command("dbuser")
def echo_database_username() -> None:
    """Print the database username"""
    print(get_database_username())


@app.command("dbtoken")
def echo_database_access_token() -> None:
    """Print the database access token"""
    print(get_database_access_token())
