"""Static features CLI"""
from enum import Enum
from typing import List
import webbrowser
import tempfile
import time
import typer
from cleanair.features import FeatureExtractor, FEATURE_CONFIG_DYNAMIC

from ..shared_args import (
    Web,
    InsertMethod,
    ValidInsertMethods,
    ValidDynamicFeatureSources,
    Sources,
    ValidSources,
)
from ..state import state

app = typer.Typer()

# pylint: disable=C0103,C0200,W0640
# Dynamically create subcommands for each feature source (e.g. ukmap)
valid_features = list(ValidDynamicFeatureSources)
valid_feature_names = []
for i in range(len(valid_features)):

    feature_source = valid_features[i]
    sub_app = typer.Typer()
    feature_names = list(
        FEATURE_CONFIG_DYNAMIC[valid_features[i].value]["features"].keys()
    )
    valid_feature_names.append(
        Enum("ValidFeatureNames", zip(feature_names, feature_names))
    )

    @sub_app.command()
    def check(
        feature_name: List[valid_feature_names[i]] = typer.Option(
            None, help="Features to process. If non given will process all",
        ),
        source: List[ValidSources] = Sources,
        only_missing: bool = typer.Option(
            False, "--only-missing", help="Only show missing data",
        ),
        web: bool = Web,
        it: int = typer.Option(i, hidden=True),
    ) -> None:
        "Check which static features have been processed"

        # Get all sources to process
        all_sources = [src.value for src in source]

        # Get all features to process
        if feature_name:
            all_feature_names = [fname.value for fname in feature_name]
        else:
            # Note: had to set i in the function call else looks up i global at runtime
            all_feature_names = [fname.value for fname in valid_feature_names[it]]

        # CLI Message
        typer.echo(f"Checking features: {all_feature_names} for sources {all_sources}")

        # Set up feature extractor
        static_feature_extractor = FeatureExtractor(
            feature_source=valid_features[it].value,
            table=FEATURE_CONFIG_DYNAMIC[valid_features[it].value]["table"],
            features=FEATURE_CONFIG_DYNAMIC[valid_features[it].value]["features"],
            secretfile=state["secretfile"],
            sources=all_sources,
        )

        # Set up features to check
        if web:
            # show in browser
            available_data = static_feature_extractor.get_static_feature_availability(
                all_feature_names, all_sources, only_missing, output_type="html"
            )

            with tempfile.NamedTemporaryFile(suffix=".html", mode="w") as tmp:
                tmp.write(
                    "<h1>Feature availability. Feature={}</h1>".format(
                        feature_source.value
                    )
                )
                tmp.write(available_data)
                tmp.write("<p>Where has_data = False there is missing data</p>")
                tmp.seek(0)
                webbrowser.open("file://" + tmp.name, new=2)
                time.sleep(1)
        else:
            available_data = static_feature_extractor.get_static_feature_availability(
                all_feature_names, all_sources, only_missing, output_type="tabulate"
            )

            print(available_data)

    @sub_app.command()
    def fill(
        feature_name: List[valid_feature_names[i]] = typer.Option(
            None, help="Features to process. If non given will process all",
        ),
        source: List[ValidSources] = Sources,
        insert_method: ValidInsertMethods = InsertMethod,
        it: int = typer.Option(i, hidden=True),
    ) -> None:
        "Process static features and insert into the database"

        # Get all sources to process
        all_sources = [src.value for src in source]

        # Get all features to process
        if feature_name:
            all_feature_names = [fname.value for fname in feature_name]
        else:
            # Note: had to set i in the function call else looks up i global at runtime
            all_feature_names = [fname.value for fname in valid_feature_names[it]]

        # CLI Message
        typer.echo(
            f"Processing features: {all_feature_names} for sources {all_sources}"
        )

        # Set up feature extractor
        static_feature_extractor = FeatureExtractor(
            feature_source=valid_features[it].value,
            table=FEATURE_CONFIG_DYNAMIC[valid_features[it].value]["table"],
            features=FEATURE_CONFIG_DYNAMIC[valid_features[it].value]["features"],
            secretfile=state["secretfile"],
            sources=all_sources,
            insert_method=insert_method.value,
        )

        # static_feature_extractor.update_remote_tables()

    app.add_typer(sub_app, name=feature_source.value)
