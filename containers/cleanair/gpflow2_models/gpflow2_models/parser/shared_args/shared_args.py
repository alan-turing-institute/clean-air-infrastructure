"""Shared CLI arguments"""
from typing import Dict, List
import os
import json
from enum import Enum
from pathlib import Path
import typer


def NDays_callback(value: int) -> int:
    "convert days to hours"
    return value * 24


def NWorkers_callback(value: int) -> int:
    "cap workers"
    if value > 6:
        raise ValueError("nworkers must be less than 7")
    return value


NHours = typer.Option(0, help="Number of hours of data to process", show_default=True)

NDays = typer.Option(
    0,
    help="Number of days of data to process",
    show_default=True,
    callback=NDays_callback,
)

InputDir = typer.Option(Path.cwd())
