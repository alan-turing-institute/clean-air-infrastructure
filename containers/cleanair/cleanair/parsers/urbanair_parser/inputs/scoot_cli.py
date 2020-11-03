"""Scoot CLI"""
import typer
from cleanair.inputs import ScootWriter, ScootReader
from cleanair.loggers import initialise_logging
from ..shared_args import UpTo, NDays, NHours, Web, AWSId, AWSKey, ScootDetectors
from ..state import state

app = typer.Typer()

# pylint: disable=W0613,W0612
@app.command()
def check(
    upto: str = UpTo,
    nhours: int = NHours,
    ndays: int = NDays,
    detectors: str = ScootDetectors,
    missing: bool = typer.Option(
        False,
        "--missing",
        help="Show missing data (i.e. data in database as null). Else show data expected but not in database",
    ),
    daily: bool = typer.Option(False, "--daily", help="Aggregate by day",),
) -> None:
    """Show percentage of scoot sensors which have data as quartiles"""

    typer.echo("Check scoot data")

    # Set logging verbosity
    # pylint: disable=W0612
    default_logger = initialise_logging(state["verbose"])

    scoot_reader = ScootReader(
        end=upto,
        nhours=nhours + ndays,
        secretfile=state["secretfile"],
        detector_ids=detectors if detectors else None,
    )

    print(
        scoot_reader.get_percentage_quantiles(
            missing=missing, daily=daily, output_type="tabulate",
        )
    )


@app.command()
def fill(
    upto: str = UpTo,
    nhours: int = NHours,
    ndays: int = NDays,
    aws_key_id: str = AWSId,
    aws_key: str = AWSKey,
    detectors: str = ScootDetectors,
) -> None:
    """Query the Scoot S3 bucket and insert into the database"""
    typer.echo("Fill scoot data")

    # Set logging verbosity
    default_logger = initialise_logging(state["verbose"])

    # Update the SCOOT reading table on the database, logging any unhandled exceptions
    scoot_writer = ScootWriter(
        end=upto,
        nhours=nhours + ndays,
        secretfile=state["secretfile"],
        aws_key_id=aws_key_id,
        aws_key=aws_key,
        detector_ids=list(detectors) if detectors else None,
    )
    scoot_writer.update_remote_tables()
