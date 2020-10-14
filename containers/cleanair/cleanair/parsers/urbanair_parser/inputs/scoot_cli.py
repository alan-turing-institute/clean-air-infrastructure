"""Scoot CLI"""
from cleanair.databases.tables import scoot_tables
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
    web: bool = Web,
    detectors: str = ScootDetectors,
) -> None:
    """Check what Scoot data is in the database"""

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

    # print(scoot_reader.scoot_detectors(output_type="sql"))

    # print(scoot_reader.gen_date_range("2020-01-01", "2020-01-02", output_type="sql"))

    # print(
    #     scoot_reader.gen_expected_readings(
    #         "2020-01-01", "2020-01-02", output_type="sql"
    #     )
    # )

    # print(
    #     scoot_reader.scoot_readings(
    #         start="2020-01-01", upto="2020-01-02", output_type="sql"
    #     )
    # )

    sd = "2020-10-01"
    ed = "2020-10-14"
    det_ids = None
    # print(
    #     scoot_reader.get_reading_status(
    #         sd, ed, detector_ids=det_ids, only_missing=False, output_type="tabulate",
    #     )
    # )

    # print(
    #     scoot_reader.get_percentage_readings_by_sensor(
    #         sd, ed, detector_ids=det_ids, group_daily=True, output_type="tabulate",
    #     )
    # )
    print(
        scoot_reader.get_percentage_readings_quantiles(
            sd, ed, detector_ids=det_ids, output_type="tabulate",
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
        detector_ids=detectors if detectors else None,
    )
    scoot_writer.update_remote_tables()
