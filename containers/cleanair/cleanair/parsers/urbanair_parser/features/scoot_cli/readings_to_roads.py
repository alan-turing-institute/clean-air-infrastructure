from typing import List
from enum import Enum
import time
import webbrowser
import tempfile
import typer
from .....loggers import initialise_logging
from .....processors import ScootPerRoadReadingMapper
from ...state import state
from ...shared_args import UpTo, NDays, NHours, Species
from .....features import ScootFeatureExtractor, FEATURE_CONFIG_DYNAMIC
from ...shared_args import (
    ValidSources,
    Sources,
    ValidDynamicFeatureSources,
    ValidInsertMethods,
    InsertMethod,
    Web,
)
from .....databases.materialised_views import LondonBoundaryView

feature_names = list(FEATURE_CONFIG_DYNAMIC["scoot"]["features"].keys())
valid_feature_names = Enum("ValidFeatureNames", zip(feature_names, feature_names))


app = typer.Typer(help="Map scoot sensor readings to road segments")


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
    """Check which road segments have scoot sensors mapped to them"""

    default_logger = initialise_logging(state["verbose"])

    insert_method = "all"
    if only_missing:
        insert_method = "missing"

    if not feature_name:
        feature_name = list(valid_feature_names)

    scoot_features = ScootFeatureExtractor(
        features=feature_name,
        sources=source,
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
):
    """Construct maps between roads and SCOOT detectors"""

    default_logger = initialise_logging(state["verbose"])

    if not feature_name:
        feature_name = list(valid_feature_names)

    scoot_features = ScootFeatureExtractor(
        features=feature_name,
        sources=source,
        insert_method=insert_method,
        end=upto,
        nhours=nhours + ndays,
        secretfile=state["secretfile"],
    )

    # print(scoot_road_readings.update_remote_tables(output_type="sql"))

    # print(
    #     scoot_features.oshighway_intersection(
    #         point_ids=["786246d4-7c6d-4017-adf2-47cabb624f8d"], output_type="sql"
    #     )
    # )

    scoot_features.update_remote_tables()
    # print(
    #     scoot_features.get_scoot_features(
    #         point_ids=[
    #             "fa6bf3a7-7448-450b-a6cb-b53694501ea8",
    #             "786246d4-7c6d-4017-adf2-47cabb624f8d",
    #             "8e3f6990-f8a9-427b-8526-2cdb19bbeb55",
    #             "f664314d-ea69-4a57-bd87-5e7cb38ec3d7",
    #             "26cd5561-9374-4b70-ac48-af25ad9f87f7",
    #             "e68bc738-66f2-461c-9988-116e4fbf7904",
    #             "9c61e592-b0f8-4cdd-86cd-aa8a092b2db0",
    #             "cb164b9e-46b9-44c0-8041-5aac4544e17d",
    #             "31b1c7a1-63e8-4d4f-ab6a-227bbe5da0b5",
    #             "42bf0950-8438-498d-8024-ea8c8f43aff9",
    #         ],
    #         start_datetime="2020-01-01T00:00:00",
    #         end_datetime="2020-01-02T00:00:00",
    #         output_type="sql",
    #     )
    # )

    # print()

    # print(
    #     scoot_features.get_scoot_feature_availability(
    #         feature_names=feature_name,
    #         sources=source,
    #         start_datetime="2020-01-01T00:00:00",
    #         end_datetime="2020-01-02T00:00:00",
    #         exclude_has_data=True,
    #         output_type="sql",
    #     )
    # )

    # scoot_features.update_remote_tables()
    # print(
    #     scoot_road_readings.get_processed_data(
    #         "2020-01-01T00:00:00", "2020-01-02T00:00:00", output_type="sql"
    #     )
    # )

    # print(scoot_road_readings.get_road_ids(output_type="list"))

    # print(
    #     scoot_road_readings.get_processed_data(
    #         road_id="osgb4000000027865913",
    #         start_datetime="2020-08-01T00:00:00",
    #         end_datetime="2020-08-05T00:00:00",
    #         output_type="sql",
    #     )
    # )

