

import typer
from cleanair.parsers.urbanair_parser.shared_args import NDays, NHours, UpTo, Tag


app = typer.Typer(help="Forecasting for Odysseus.")

@app.command()
def scoot(
    fit_start_time: str = typer.Option("today", help="Date(time) when the models were trained."),
    forecast_days: int = NDays,
    forecast_hours: int = NHours,
    forecast_upto: str = UpTo,
    tag: str = Tag,
) -> None:
    """Forecast a GP on a Scoot data."""
    # TODO 1. use the tag and fit_start_time to query the database for the instance ids
    # TODO 2. from the instance ids load the models
    # TODO 3. from the instance ids get the data ids
    # TODO 4. from the data ids get the detectors each instance was trained on (and will be forecast upon) and the preprocessing settings
    # TODO 5. create a new data config from the detectors and the forecast days/upto
    # TODO 6. from the data config and preprocessing create a new data id and an X to predict upon
    # TODO 7. forecast on the new X
    # TODO 8. write the forecast to the results table using the instance id and the new data id
    raise NotImplementedError("See TODOs for implementation instructions")
