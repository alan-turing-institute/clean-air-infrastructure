import typer
from ...state import state
from .....loggers import initialise_logging
from .....processors import ScootPerRoadDetectors

app = typer.Typer(help="Map scoot sensors to roads")


@app.command()
def check():
    """Check which road segments have scoot sensors mapped to them"""

    default_logger = initialise_logging(state["verbose"])

    default_logger.warning("Not yet implemented")

    raise typer.Abort()


@app.command()
def fill():
    """Construct maps between roads and SCOOT detectors"""

    # Update the SCOOT roadmap table on the database, logging any unhandled exceptions
    try:
        road_mapper = ScootPerRoadDetectors(secretfile=args.secretfile)
        # Match all road segments to their closest SCOOT detector(s)
        # - if the segment has detectors on it then match to them
        # - otherwise match to the five closest detectors
        road_mapper.update_remote_tables()

    except Exception as error:
        default_logger.error("An uncaught exception occurred: %s", str(error))
        raise
