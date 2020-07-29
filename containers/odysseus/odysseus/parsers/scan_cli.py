"""CLI for scan stats."""

import typer
from cleanair.parsers.urbanair_parser.shared_args import (
	NDays,
	NHours,
	UpTo,
)
from cleanair.parsers.urbanair_parser.state import state
from .shared_args import Borough, GridResolution, ModelName
from ..scoot import ScanScoot

app = typer.Typer()

@app.command()
def scoot(
	borough: str = Borough,
	grid_resolution: int = GridResolution,
	forecast_days: int = NDays,
	forecast_hours: int = NHours,
	model_name: str = ModelName,
	train_days: int = NDays,
	train_hours: int = NHours,
	upto: str = UpTo,
) -> None:
	"""Run scan stats on scoot."""
	secretfile: str = state["secretfile"]
	# NOTE days converted to hours with ndays callback
	train_hours = train_days + train_hours
	forecast_hours = forecast_days + forecast_hours

	# run the scan stats
	scan_scoot = ScanScoot(borough, forecast_hours, train_hours, upto, grid_resolution=grid_resolution, model_name=model_name, secretfile=secretfile)
	scan_df = scan_scoot.run()