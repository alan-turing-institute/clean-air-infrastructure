from typing import List
from enum import Enum
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
)

from .....databases.materialised_views import LondonBoundaryView

app = typer.Typer(help="Map scoot sensor readings to road segments")

feature_names = list(FEATURE_CONFIG_DYNAMIC["scoot"]["features"].keys())
valid_feature_names = Enum("ValidFeatureNames", zip(feature_names, feature_names))

print(feature_names)
print(list(valid_feature_names))
# feature_source = valid_features[i]

# sub_app = typer.Typer()
# feature_names = list(FEATURE_CONFIG[valid_features[i].value]["features"].keys())
# valid_feature_names.append(Enum("ValidFeatureNames", zip(feature_names, feature_names)))


@app.command()
def check():
    """Check which road segments have scoot sensors mapped to them"""

    default_logger = initialise_logging(state["verbose"])

    default_logger.warning("Not yet implemented")

    raise typer.Abort()


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

    # Get all sources to process
    all_sources = [src.value for src in source]

    # Get all features to process
    if feature_name:
        all_feature_names = [fname.value for fname in feature_name]
    else:
        # Note: had to set i in the function call else looks up i global at runtime
        all_feature_names = [fname.value for fname in valid_feature_names]

    default_logger = initialise_logging(state["verbose"])

    scoot_features = ScootFeatureExtractor(
        features=all_feature_names,
        sources=all_sources,
        insert_method=insert_method,
        secretfile=state["secretfile"],
    )

    # print(scoot_road_readings.update_remote_tables(output_type="sql"))

    # print(
    #     scoot_features.oshighway_intersection(
    #         point_ids=["786246d4-7c6d-4017-adf2-47cabb624f8d"], output_type="sql"
    #     )
    # )

    print(
        scoot_features.get_scoot_features(
            point_ids=[
                "fa6bf3a7-7448-450b-a6cb-b53694501ea8",
                "786246d4-7c6d-4017-adf2-47cabb624f8d",
                "8e3f6990-f8a9-427b-8526-2cdb19bbeb55",
                "f664314d-ea69-4a57-bd87-5e7cb38ec3d7",
                "26cd5561-9374-4b70-ac48-af25ad9f87f7",
                "e68bc738-66f2-461c-9988-116e4fbf7904",
                "9c61e592-b0f8-4cdd-86cd-aa8a092b2db0",
                "cb164b9e-46b9-44c0-8041-5aac4544e17d",
                "31b1c7a1-63e8-4d4f-ab6a-227bbe5da0b5",
                "42bf0950-8438-498d-8024-ea8c8f43aff9",
            ],
            start_datetime="2020-01-01T00:00:00",
            end_datetime="2020-01-02T00:00:00",
            output_type="sql",
        )
    )

    print()

    print(
        scoot_features.get_scoot_feature_availability(
            feature_names=all_feature_names,
            sources=all_sources,
            start_datetime="2020-01-01T00:00:00",
            end_datetime="2020-01-02T00:00:00",
            exclude_has_data=True,
            output_type="sql",
        )
    )
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

