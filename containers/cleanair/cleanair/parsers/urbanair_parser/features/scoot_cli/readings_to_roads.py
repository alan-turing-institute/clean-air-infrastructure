import typer
from .....loggers import initialise_logging
from .....processors import ScootPerRoadReadingMapper
from ...state import state
from ...shared_args import UpTo, NDays, NHours, Species

app = typer.Typer(help="Map scoot sensor readings to road segments")


@app.command()
def check():
    """Check which road segments have scoot sensors mapped to them"""

    default_logger = initialise_logging(state["verbose"])

    default_logger.warning("Not yet implemented")

    raise typer.Abort()


@app.command()
def fill(upto: str = UpTo, nhours: int = NHours, ndays: int = NDays):
    """Construct maps between roads and SCOOT detectors"""

    default_logger = initialise_logging(state["verbose"])

    scoot_road_readings = ScootPerRoadReadingMapper(
        nhours=nhours + ndays, end=upto, secretfile=state["secretfile"]
    )

    print(scoot_road_readings.update_remote_tables(output_type="sql"))

    # print(
    #     scoot_road_readings.get_processed_data(
    #         "2020-01-01T00:00:00", "2020-01-02T00:00:00", output_type="sql"
    #     )
    # )

    # print(scoot_road_readings.get_road_ids(output_type="list"))

    # print(
    #     scoot_road_readings.get_processed_data(
    #         road_id="osgb4000000027865913",
    #         start_datetime="2020-08-01T00:00:00",
    #         end_datetime="2020-08-05T00:00:00",
    #         output_type="sql",
    #     )
    # )

