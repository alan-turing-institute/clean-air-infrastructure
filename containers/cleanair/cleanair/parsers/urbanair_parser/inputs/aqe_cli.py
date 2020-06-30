import typer
from cleanair.inputs import AQEWriter
from cleanair.loggers import initialise_logging
from datetime import datetime
from ..shared_args import UpTo, NDays, NHours
from ..state import state

app = typer.Typer()


@app.command()
def check(upto: str = UpTo, nhours: int = NHours, ndays: int = NDays) -> None:
    typer.echo("Not Yet Implimented")


@app.command()
def fill(upto: str = UpTo, nhours: int = NHours, ndays: int = NDays) -> None:

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
