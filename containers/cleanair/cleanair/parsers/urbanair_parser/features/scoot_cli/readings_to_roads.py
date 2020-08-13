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
