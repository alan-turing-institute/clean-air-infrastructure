"""LAQN input cli"""
from typing import List
import typer
from cleanair.inputs import LAQNWriter
from cleanair.loggers import initialise_logging
from cleanair.types import Species as ValidSpecies
from ..shared_args import UpTo, NDays, NHours, Species
from ..state import state

app = typer.Typer()

# pylint: disable=W0613
@app.command()
def check(
    upto: str = UpTo,
    nhours: int = NHours,
    ndays: int = NDays,
    species: List[ValidSpecies] = Species,
) -> None:
    """Check what LAQN data is in the database"""

    all_species = [spc.value for spc in species]

    # Set logging verbosity
    default_logger = initialise_logging(state["verbose"])

    laqn_writer = LAQNWriter(
        end=upto, nhours=nhours + ndays, secretfile=state["secretfile"]
    )

    # print(laqn_writer.get_open_sites(output_type="sql",))

    # print(laqn_writer.get_open_sites(output_type="tabulate",))

    # print(
    #     laqn_writer.get_raw_data(
    #         start_date=laqn_writer.start_datetime.isoformat(),
    #         end_date=laqn_writer.end_datetime.isoformat(),
    #         species=all_species,
    #         output_type="sql",
    #     )
    # )

    # print(
    #     laqn_writer.get_raw_data(
    #         start_date=laqn_writer.start_datetime.isoformat(),
    #         end_date=laqn_writer.end_datetime.isoformat(),
    #         species=all_species,
    #         output_type="tabulate",
    #     )
    # )

    # print(
    #     laqn_writer.gen_date_range(
    #         start_date=laqn_writer.start_datetime.isoformat(),
    #         end_date=laqn_writer.end_datetime.isoformat(),
    #         species=all_species,
    #         output_type="sql",
    #     )
    # )

    # print(
    #     laqn_writer.gen_date_range(
    #         start_date=laqn_writer.start_datetime.isoformat(),
    #         end_date=laqn_writer.end_datetime.isoformat(),
    #         species=all_species,
    #         output_type="tabulate",
    #     )
    # )

    # print(
    #     laqn_writer.get_laqn_availability(
    #         start_date=laqn_writer.start_datetime.isoformat(),
    #         end_date=laqn_writer.end_datetime.isoformat(),
    #         species=all_species,
    #         output_type="sql",
    #     )
    # )

    # print(
    #     laqn_writer.get_laqn_availability(
    #         start_date=laqn_writer.start_datetime.isoformat(),
    #         end_date=laqn_writer.end_datetime.isoformat(),
    #         species=all_species,
    #         output_type="tabulate",
    #     )
    # )

    # print(
    #     laqn_writer.get_laqn_availability_daily(
    #         start_date=laqn_writer.start_datetime.isoformat(),
    #         end_date=laqn_writer.end_datetime.isoformat(),
    #         species=all_species,
    #         output_type="sql",
    #     )
    # )

    # print(
    #     laqn_writer.get_laqn_availability_daily(
    #         start_date=laqn_writer.start_datetime.isoformat(),
    #         end_date=laqn_writer.end_datetime.isoformat(),
    #         species=all_species,
    #         output_type="tabulate",
    #     )
    # )

    # print(
    #     laqn_writer.get_laqn_availability_daily_total(
    #         start_date=laqn_writer.start_datetime.isoformat(),
    #         end_date=laqn_writer.end_datetime.isoformat(),
    #         species=all_species,
    #         output_type="sql",
    #     )
    # )

    print(
        laqn_writer.get_laqn_availability_daily_total(
            start_date=laqn_writer.start_datetime.isoformat(),
            end_date=laqn_writer.end_datetime.isoformat(),
            species=all_species,
            output_type="tabulate",
        )
    )


@app.command()
def fill(upto: str = UpTo, nhours: int = NHours, ndays: int = NDays) -> None:
    """Query the LAQN API and insert into the database"""
    typer.echo("Fill LAQN inputs")

    # Set logging verbosity
    default_logger = initialise_logging(state["verbose"])

    # Update the LAQN tables on the database, logging any unhandled exceptions
    try:
        laqn_writer = LAQNWriter(
            end=upto, nhours=nhours + ndays, secretfile=state["secretfile"]
        )
        laqn_writer.update_remote_tables()
    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise
