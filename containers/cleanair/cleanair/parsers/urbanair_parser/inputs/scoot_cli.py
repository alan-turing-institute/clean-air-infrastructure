"""Scoot CLI"""
import typer
from cleanair.inputs import ScootWriter
from cleanair.loggers import initialise_logging
from ..shared_args import UpTo, NDays, NHours, Web, AWSId, AWSKey
from ..state import state

app = typer.Typer()

# pylint: disable=W0613
@app.command()
def check(
    upto: str = UpTo, nhours: int = NHours, ndays: int = NDays, web: bool = Web
) -> None:
    """Check what Scoot data is in the database"""

    typer.echo("Check scoot data")
    # Set logging verbosity
    default_logger = initialise_logging(state["verbose"])


@app.command()
def fill(
    upto: str = UpTo,
    nhours: int = NHours,
    ndays: int = NDays,
    aws_key_id: str = AWSId,
    aws_key: str = AWSKey,
) -> None:
    """Query the Scoot S3 bucket and insert into the database"""
    typer.echo("Fill scoot data")

    # Set logging verbosity
    default_logger = initialise_logging(state["verbose"])

    # Update the SCOOT reading table on the database, logging any unhandled exceptions
    try:
        scoot_writer = ScootWriter(
            end=upto,
            nhours=nhours + ndays,
            secretfile=state["secretfile"],
            aws_key_id=aws_key_id,
            aws_key=aws_key,
        )
        scoot_writer.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise