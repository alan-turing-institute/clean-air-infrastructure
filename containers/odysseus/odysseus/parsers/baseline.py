"""Commands for running the percent of baseline metric."""

from datetime import datetime
from dateutil.parser import isoparse
import typer
from odysseus.scoot_processing import TrafficPercentageChange
from odysseus.dates import (
    LOCKDOWN_BASELINE_END,
    NORMAL_BASELINE_END,
)
from cleanair.parsers.urbanair_parser.shared_args import (
    NDays,
    UpTo,
)
from cleanair.parsers.urbanair_parser.state import state

app = typer.Typer(help="Percent of baseline.")


@app.command()
def scoot(
    backfill: bool = typer.Option(False), ndays: int = NDays, upto: str = UpTo,
) -> None:
    """Percent of baseline for scoot."""
    secretfile: str = state["secretfile"]

    if backfill:
        # Calculate how many days are backfillable
        ndays_lockdown = (datetime.today() - isoparse(LOCKDOWN_BASELINE_END)).days
        ndays_normal = (datetime.today() - isoparse(NORMAL_BASELINE_END)).days

        # get query object
        traffic_query_normal = TrafficPercentageChange(
            secretfile=secretfile,
            end=upto,
            nhours=(ndays_normal * 24) - 24,
            baseline_tag="normal",
        )

        traffic_query_lockdown = TrafficPercentageChange(
            secretfile=secretfile,
            end=upto,
            nhours=(ndays_lockdown * 24) - 24,
            baseline_tag="lockdown",
        )

    else:
        # get query object
        traffic_query_normal = TrafficPercentageChange(
            secretfile=secretfile, end=upto, nhours=ndays - 24, baseline_tag="normal",
        )

        traffic_query_lockdown = TrafficPercentageChange(
            secretfile=secretfile,
            end=upto,
            nhours=(ndays) - 24,
            baseline_tag="lockdown",
        )

    traffic_query_lockdown.update_remote_tables()
    traffic_query_normal.update_remote_tables()
