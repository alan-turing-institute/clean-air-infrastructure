"""Shared CLI arguments"""
from typing import Dict, List
import os
import json
from enum import Enum
import typer
from ..state import DATA_CACHE
from ....features import FEATURE_CONFIG, FEATURE_CONFIG_DYNAMIC
from ....timestamps import as_datetime, TIMESTRINGS
from ....types import Source as ValidSources


# pylint: disable=C0103
zip_features: Dict = dict(zip(FEATURE_CONFIG.keys(), FEATURE_CONFIG.keys()))
zip_features_dynamic: Dict = dict(
    zip(FEATURE_CONFIG_DYNAMIC.keys(), FEATURE_CONFIG_DYNAMIC.keys())
)
ValidFeatureSources = Enum("ValidFeatureSources", zip_features)
ValidDynamicFeatureSources = Enum("ValidDynamicFeatureSources", zip_features_dynamic)

DEFAULT_SOURCES = [ValidSources.laqn, ValidSources.aqe]


class ValidInsertMethods(str, Enum):
    "Valid insert methods"
    missing = "missing"
    all = "all"


def UpTo_callback(value: str) -> str:
    "process UpTo arg"
    try:
        return as_datetime(value).isoformat()
    except ValueError:
        raise typer.BadParameter(
            f"Value must be a iso datetime of the form %Y-%m-%d, %Y-%m-%dT%H:%M:%S. Or in {TIMESTRINGS}"
        )


def NDays_callback(value: int) -> int:
    "convert days to hours"
    return value * 24


def NWorkers_callback(value: int) -> int:
    if value > 2:
        raise ValueError("nworkers must be less than 3")
    return value


def CommaSeparate_callback(values: str) -> List[str]:
    "Convert comma-separated string into list"
    return [item for item in values.split(",") if item]


def CopernicusKey_callback(value: str) -> str:
    "Process CopernicusKey arg"
    if value == "":
        try:
            with open(
                os.path.abspath(
                    os.path.join(os.sep, "secrets", "copernicus_secrets.json")
                )
            ) as f_secret:
                data = json.load(f_secret)
                value = data["copernicus_key"]
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            raise typer.BadParameter(
                "Copernicus key not provided and could not find in 'secrets/copernicus_secrets.json'"
            )

    return value


def AWSID_callback(value: str) -> str:
    "Process AWSID arg"
    if value == "":
        try:
            with open(
                os.path.abspath(os.path.join(os.sep, "secrets", "aws_secrets.json"))
            ) as f_secret:
                data = json.load(f_secret)
                return data["aws_key_id"]
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            raise typer.BadParameter(
                "aws-key-id not provided and could not be found in 'secrets/aws_secrets.json'"
            )

    return value


def AWSKey_callback(value: str) -> str:
    "Process AWSKey arg"
    if value == "":
        try:
            with open(
                os.path.abspath(os.path.join(os.sep, "secrets", "aws_secrets.json"))
            ) as f_secret:
                data = json.load(f_secret)
                return data["aws_key"]
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            raise typer.BadParameter(
                "aws-key not provided and could not be found in 'secrets/aws_secrets.json'"
            )
    return value


From = typer.Option(
    "tomorrow",
    help=f"which datetime to start process data from. Must be either an ISO datetime or one of {TIMESTRINGS}",
    callback=UpTo_callback,
    show_default=True,
)

UpTo = typer.Option(
    "tomorrow",
    help=f"up to what datetime to process data. Must be either an ISO datetime or one of {TIMESTRINGS}",
    callback=UpTo_callback,
    show_default=True,
)

NHours = typer.Option(0, help="Number of hours of data to process", show_default=True)

NDays = typer.Option(
    0,
    help="Number of days of data to process",
    show_default=True,
    callback=NDays_callback,
)

CopernicusKey = typer.Option(
    "",
    help="Copernicus API key. If not provided will try to load from 'secrets/copernicus_secrets.json'",
    callback=CopernicusKey_callback,
)

Web = typer.Option(False, help="Show outputs in browser", show_default=True,)

InputDir = typer.Argument(
    DATA_CACHE,
    dir_okay=True,
    file_okay=False,
    writable=True,
    readable=True,
    resolve_path=True,
    exists=False,
)

InsertMethod = typer.Option(
    ValidInsertMethods.missing,
    help="Only missing data or process all data",
    show_default=True,
)

AWSId = typer.Option(
    "", help="AWS key ID for accessing TfL SCOOT data", callback=AWSID_callback
)

AWSKey = typer.Option(
    "", help="AWS key for accessing TfL SCOOT data", callback=AWSKey_callback
)

ScootDetectors = typer.Option(
    "",
    help="Comma-separated string of SCOOT detectors to forecast for  [default: all of them]",
    callback=CommaSeparate_callback,
    show_default=False,
)

Sources = typer.Option(..., help="List sources to process")

Species = typer.Option(..., help="Species of pollutant")

NWorkers = typer.Option(
    1,
    show_default=True,
    help="Number of threads and database cores to use",
    callback=NWorkers_callback,
)
