"""Shared CLI arguments"""
import os
import json
from enum import Enum
import typer
from dateutil.parser import isoparse
from cleanair.features import FEATURE_CONFIG, ALL_FEATURES

UP_TO_VALUES = ["lasthour", "now", "today", "tomorrow", "yesterday"]

# pylint: disable=C0103
ValidFeatureSources = Enum(
    "ValidFeatureSources", dict(zip(FEATURE_CONFIG.keys(), FEATURE_CONFIG.keys()))
)
ValidFeatureNames = Enum("ValidFeatureNames", dict(zip(ALL_FEATURES, ALL_FEATURES)))


class ValidSources(str, Enum):
    "Valid sources"
    laqn = "laqn"
    aqe = "aqe"
    satellite = "satellite"
    hexgrid = "hexgrid"


DEFAULT_SOURCES = [ValidSources.laqn, ValidSources.aqe]


class ValidInsertMethods(str, Enum):
    "Valid insert methods"
    missing = "missing"
    all = "all"


def is_iso_string(isostring: str) -> bool:
    """Check if isostring is a valid iso string

        Arguments:
            isostring (str): An iso string
        """
    try:
        isoparse(isostring)
    except ValueError:
        return False

    return True


def UpTo_callback(value: str) -> str:
    "process UpTo arg"
    if (value in UP_TO_VALUES) or is_iso_string(value):
        return value

    raise typer.BadParameter(
        f"Value must be a iso datetime of the form %Y-%m-%d, %Y-%m-%dT%H:%M:%S. Or in {UP_TO_VALUES}"
    )


def NDays_callback(value: int) -> int:
    "convert days to hours"
    return value * 24


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


UpTo = typer.Option(
    "tomorrow",
    help=f"up to what datetime to process data. Must be iso datetime or in {UP_TO_VALUES}",
    callback=UpTo_callback,
    show_default=True,
)

NHours = typer.Option(0, help="Number of hours of data to process", show_default=True)

NDays = typer.Option(
    1,
    help="Number of days of data to process",
    callback=NDays_callback,
    show_default=True,
)

CopernicusKey = typer.Option(
    "",
    help="Copernicus API key. If not provided will try to load from 'secrets/copernicus_secrets.json'",
    callback=CopernicusKey_callback,
)

Web = typer.Option(False, help="Show outputs in browser", show_default=True,)

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

Sources = typer.Option(..., help="List sources to process")
