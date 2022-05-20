"""CLI for querying metrics"""

import typer

from ....metrics import AirQualityMetricsQuery
from ..state import state
from ....types import Source

app = typer.Typer(name="metrics")


@app.command()
def spatial(instance_id: str) -> None:
    """Print the spatial metrics for the instance"""
    secretfile: str = state["secretfile"]
    metrics_query = AirQualityMetricsQuery(secretfile=secretfile)
    spatial_metrics = metrics_query.query_spatial_metrics(
        instance_id, Source.laqn, output_type="tabulate"
    )
    print(spatial_metrics)


@app.command()
def temporal(instance_id: str) -> None:
    """Print the temporal metrics for the instance"""
    secretfile: str = state["secretfile"]
    metrics_query = AirQualityMetricsQuery(secretfile=secretfile)
    temporal_metrics = metrics_query.query_temporal_metrics(
        instance_id, Source.laqn, output_type="tabulate"
    )
    print(temporal_metrics)
