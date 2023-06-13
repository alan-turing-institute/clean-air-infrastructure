"""Initialising a CLI app from the callback."""

import typer
from ..state import (
    state,
    CONFIG_SECRETFILE_PATH,
    APP_DIR,
    DATA_CACHE,
)
from ....loggers import initialise_logging


def init_callback(
    verbose: bool = False,
    secretfile: str = typer.Option(
        None,
        help="json file containing database secrets. Not required if an init command called",
    ),
) -> None:
    """
    Manage the CleanAir infrastructure
    """

    # Create app directory structure
    if not APP_DIR.is_dir():
        typer.echo("Creating Urbanair CLI application directory")
        APP_DIR.mkdir(parents=True)

    if not DATA_CACHE.is_dir():
        DATA_CACHE.mkdir()

    # Configure settings
    if verbose:
        typer.echo("Debug verbosity")
        state["verbose"] = True

    if secretfile:
        state["secretfile"] = secretfile
        return

    if CONFIG_SECRETFILE_PATH.is_file():
        state["secretfile"] = CONFIG_SECRETFILE_PATH

    # Set logging verbosity
    default_logger = initialise_logging(state["verbose"])

    state["logger"] = default_logger
