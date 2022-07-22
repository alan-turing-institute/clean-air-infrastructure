"""Configurations for urbanair."""

import typer
import logging
from typing import Callable, List, Optional
from pathlib import Path
from logging import Logger
from typing import Callable, List, Optional


from ....types.enum_types import ClusterId
from ..shared_args import DataConfig
from ..state import state
from ....loggers import initialise_logging


app = typer.Typer(help="Experiment CLI")


def download(
    cluster_id: ClusterId = ClusterId.nc6,
    download_root: Path = DataConfig,
    instance_root: Optional[Path] = None,
    verbose: bool = False,
) -> None:
    """Setup an experiment: load data"""
    secretfile: str = state["secretfile"]
    initialise_logging(verbose)  # set logging level
