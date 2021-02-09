"Scoot feature processing cli"
from typing import List
from enum import Enum
import time
import webbrowser
import tempfile
import typer
from ....loggers import initialise_logging
from ..state import state
from ..shared_args import UpTo, NDays, NHours, NWorkers
from ....features import (
    ScootFeatureExtractor,
    FEATURE_CONFIG_DYNAMIC,
)
from ..shared_args import (
    ValidSources,
    Sources,
    ValidInsertMethods,
    InsertMethod,
    Web,
)
from ....processors import ScootPerRoadDetectors

# pylint: disable=C0103,C0200,W0640,R0913,W0612
feature_names = list(FEATURE_CONFIG_DYNAMIC["scoot"]["features"].keys())
valid_feature_names = Enum("ValidFeatureNames", zip(feature_names, feature_names))


app = typer.Typer(help="Process Scoot features")


@app.command()
def check(
    upto: str = UpTo,
    nhours: int = NHours,
    ndays: int = NDays,
    feature_name: List[valid_feature_names] = typer.Option(
        None, help="Features to process. If non given will process all",
    ),
    source: List[ValidSources] = Sources,
    only_missing: bool = typer.Option(
        False, "--only-missing", help="Only show missing data",
    ),
    web: bool = Web,
):
    """Check which scoot features have been processed"""

    default_logger = initialise_logging(state["verbose"])

    insert_method = "all"
    if only_missing:
        insert_method = "missing"

    if not feature_name:
        feature_name = list(valid_feature_names)

    scoot_features = ScootFeatureExtractor(
        features=feature_name,
        sources=source,
        n_workers=1,
        insert_method=insert_method,
        end=upto,
        nhours=nhours + ndays,
        secretfile=state["secretfile"],
    )

    # Set up features to check
    if web:
        # show in browser
        available_data = scoot_features.check_remote_table(output_type="html")

        with tempfile.NamedTemporaryFile(suffix=".html", mode="w") as tmp:
            tmp.write(
                f"<h1>Feature availability for features: {[feat.value for feat in feature_name]}"
            )
            tmp.write(available_data)
            tmp.write("<p>Where has_data = False there is missing data</p>")
            tmp.seek(0)
            webbrowser.open("file://" + tmp.name, new=2)
            time.sleep(1)
    else:
        available_data = scoot_features.check_remote_table(output_type="tabulate")

        print(available_data)


@app.command()
def fill(
    upto: str = UpTo,
    nhours: int = NHours,
    ndays: int = NDays,
    feature_name: List[valid_feature_names] = typer.Option(
        None, help="Features to process. If non given will process all",
    ),
    source: List[ValidSources] = Sources,
    insert_method: ValidInsertMethods = InsertMethod,
    nworkers: int = NWorkers,
    readings: bool = typer.Option(
        False,
        "--use-readings",
        help="Use raw scoot readings instead of scoot forecasts",
    ),
):
    """Process scoot features"""

    default_logger = initialise_logging(state["verbose"])

    if not feature_name:
        feature_name = list(valid_feature_names)

    scoot_features = ScootFeatureExtractor(
        features=feature_name,
        sources=source,
        n_workers=nworkers,
        insert_method=insert_method,
        end=upto,
        nhours=nhours + ndays,
        forecast=not readings,
        secretfile=state["secretfile"],
        threadsafe=True,
    )

    scoot_features.update_remote_tables()


@app.command()
def update_road_maps():
    """
    Construct maps between roads and SCOOT detectors
    """

    road_mapper = ScootPerRoadDetectors(secretfile=state["secretfile"])
    # Match all road segments to their closest SCOOT detector(s)
    # - if the segment has detectors on it then match to them
    # - otherwise match to the five closest detectors
    road_mapper.update_remote_tables()
