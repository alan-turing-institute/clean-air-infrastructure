"""Evaluate metrics on odysseus models."""

import typer

app = typer.Typer()

@app.command()
def scoot() -> None:
    """Evaluate a Gaussian Process Regression model on scoot.""" 

    # TODO 1. get experiment class from the tag and fit_start_time
    # TODO 2. using the instance ids get all the forecasts for each of those instance ids
    # TODO 3. look up the data id in the data_config table from the forecast table using instance id
    # TODO 4. from the data id get the data config and load the datasets
    # TODO 5. calculate the metrics between the forecast and observations
    # TODO 6. write the metrics to the database using the instance id and data id
    raise NotImplementedError("See TODO items in comments.")
