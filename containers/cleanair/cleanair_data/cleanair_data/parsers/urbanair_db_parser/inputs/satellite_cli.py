"""Satellite input cli"""
import webbrowser
import tempfile
import time
import typer
from cleanair_data.inputs import SatelliteWriter
from cleanair_data.loggers import initialise_logging
from ..shared_args import (
    UpTo,
    NDays,
    NHours,
    CopernicusKey,
    Web,
    InsertMethod,
    ValidInsertMethods,
)
from ..state import state

app = typer.Typer()


@app.command()
def check(
    upto: str = UpTo, nhours: int = NHours, ndays: int = NDays, web: bool = Web
) -> None:
    "Check what satellite data is in the database"
    typer.echo("Check satellite data")

    # Set logging verbosity
    # pylint: disable=W0612
    default_logger = initialise_logging(state["verbose"])

    satellite_writer = SatelliteWriter(
        copernicus_key=None,
        end=upto,
        nhours=nhours + ndays,
        secretfile=state["secretfile"],
    )

    if web:
        available_data = satellite_writer.get_satellite_availability(
            reference_start_date=satellite_writer.start_date.isoformat(),
            reference_end_date=satellite_writer.end_date.isoformat(),
            output_type="html",
        )

        with tempfile.NamedTemporaryFile(suffix=".html", mode="w") as tmp:
            tmp.write("<h1>Satellite data availability</h1>")
            tmp.write(available_data)
            tmp.write("<p>Where has_data = False there is missing data</p>")
            tmp.seek(0)
            webbrowser.open("file://" + tmp.name, new=2)
            time.sleep(1)
    else:
        available_data = satellite_writer.get_satellite_availability(
            reference_start_date=satellite_writer.start_date.isoformat(),
            reference_end_date=satellite_writer.end_date.isoformat(),
            output_type="tabulate",
        )

        typer.echo(available_data)


@app.command()
def fill(
    upto: str = UpTo,
    nhours: int = NHours,
    ndays: int = NDays,
    copernicus_key: str = CopernicusKey,
    insert_method: ValidInsertMethods = InsertMethod,
) -> None:
    "Query satellite API and insert into database"
    typer.echo(f"Fill satellite data using '{insert_method.value}' insert method")

    # Set logging verbosity
    # pylint: disable=W0612
    default_logger = initialise_logging(state["verbose"])

    satellite_writer = SatelliteWriter(
        copernicus_key=copernicus_key,
        end=upto,
        nhours=nhours + ndays,
        secretfile=state["secretfile"],
        method=insert_method.value,
    )

    satellite_writer.update_remote_tables()
