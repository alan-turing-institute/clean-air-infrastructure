"""AQE input CLI"""
import typer
from cleanair.inputs import AQEWriter
from cleanair.loggers import initialise_logging
from ..shared_args import UpTo, NDays, NHours
from ..state import state

app = typer.Typer()

# pylint: disable=W0613
@app.command()
def check(upto: str = UpTo, nhours: int = NHours, ndays: int = NDays) -> None:
    """Check what AQE data is in the database"""
    typer.echo("Not Yet Implimented")


@app.command()
def fill(upto: str = UpTo, nhours: int = NHours, ndays: int = NDays) -> None:
    """Query the AQE API and insert into the database"""

    typer.echo("Fill AQE inputs")

    # Set logging verbosity
    default_logger = initialise_logging(state["verbose"])

    # Update the AQE tables on the database, logging any unhandled exceptions
    try:
        aqe_writer = AQEWriter(
            end=upto, nhours=nhours + ndays, secretfile=state["secretfile"]
        )
        aqe_writer.update_remote_tables()
    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise
