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
    download_root: Path,
    verbose: bool = False,
) -> None:
    """Setup an experiment: load data"""
    secretfile: str = state["secretfile"]
    initialise_logging(verbose)  # set logging level
    # mkdir look
    download_root.mkdir(parents=True, exist_ok=False)
