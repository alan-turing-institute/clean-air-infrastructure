"""BL input cli"""

from typing import List
import typer
from ....inputs import BreatheWriter
from ....loggers import initialise_logging
from ....types import Species as ValidSpecies
from ..shared_args import UpTo, NDays, NHours, Species
from ..state import state

app = typer.Typer()


@app.command()
def check(upto: str = UpTo, nhours: int = NHours, ndays: int = NDays) -> None:
    """Check what AQE data is in the database"""
    typer.echo("Not Yet Implimented")


@app.command()
def fill(upto: str = UpTo, nhours: int = NHours, ndays: int = NDays) -> None:
    """Query the Breathe API and insert into the database"""
    typer.echo("Fill BreatheLondon inputs")

    # Set logging verbosity
    default_logger = initialise_logging(state["verbose"])

    # Update the Breathe tables on the database, logging any unhandled exceptions
    try:
        breathe_writer = BreatheWriter(
            end=upto, nhours=nhours + ndays, secretfile=state["secretfile"]
        )
        breathe_writer.update_remote_tables()
    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise
