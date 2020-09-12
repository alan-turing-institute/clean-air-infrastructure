"""
Given a model data object, check that the data matches the config.

download_training_config_data
download_source_data

get_training_data_inputs
get_prediction_data_inputs

---
get_static_features
get_laqn_readings
get_aqe_readings
get_satellite_readings
---

"""

from typing import List
import pytest
from enum import Enum
import uuid
from dateutil.parser import isoparse
from datetime import timedelta
from pydantic import ValidationError
from cleanair.models import ModelConfig, StaticFeatureTimeSpecies
from cleanair.types.dataset_types import DataConfig, FullDataConfig

from cleanair.types import Species, Source, FeatureNames, FeatureBufferSize
from cleanair.databases import DBWriter
from cleanair.databases.tables import MetaPoint
from cleanair.exceptions import MissingFeatureError, MissingSourceError


@pytest.fixture()
def point_ids_all(meta_records):
    "Return a function which gets all points ids for a given source"

    def _point_ids_all(source):
        return [i.id for i in meta_records if i.source == source]

    return _point_ids_all


@pytest.fixture()
def point_ids_valid(meta_within_london):
    "All laqn points for sites that are open and in London"

    def _point_ids_valid(source):
        return [i.id for i in meta_within_london if i.source == source]

    return _point_ids_valid


class TestModelData:
    def test_setup(self, fake_cleanair_dataset):
        """Insert test data"""

        pass

    @pytest.mark.parametrize("source", [Source.laqn, Source.aqe, Source.satellite])
    def test_select_static_features(
        self,
        model_data,
        point_ids_all,
        point_ids_valid,
        valid_full_config_dataset,
        source,
    ):
        """
        Test that we get the correct static features.
        Should return static features for interest points that are 
        in London and Open (for LAQN and AQE)
        """

        # Id's from config file
        config_ids = valid_full_config_dataset.train_interest_points[source]

        # Request static features
        dat = model_data.select_static_features(
            config_ids, [FeatureNames.building_height, FeatureNames.grass], source
        ).all()

        returned_static_features = {i[0].point_id for i in dat}

        if source != Source.satellite:
            # Check we get the subset of ids that are open and withing the London Boundary
            assert set(point_ids_valid(source)) == returned_static_features

        # Check we don't get all point ids
        assert set(point_ids_all(source)) != returned_static_features

        # Check this is the set of ids that ModelConfig.generate_full_config() returns
        assert set(config_ids) == {str(i) for i in returned_static_features}

    @pytest.mark.parametrize("source", [Source.laqn, Source.aqe])
    @pytest.mark.parametrize(
        "species", [[Species.NO2], [Species.PM10], [Species.NO2, Species.PM10]]
    )
    def test_select_static_time_species(
        self, model_data, valid_full_config_dataset, point_ids_valid, source, species
    ):
        """
        Test that we can cross join ModelData.select_static_features
        with a range of datetimes and species
        """

        # Id's from config file
        config_ids = valid_full_config_dataset.train_interest_points[source]
        start_datetime = valid_full_config_dataset.train_start_date
        end_datetime = valid_full_config_dataset.train_end_date

        features = [FeatureNames.building_height, FeatureNames.grass]
        # Return Pydantic model types
        static_species_time = model_data.get_static_features(
            start_datetime,
            end_datetime,
            features,
            source,
            config_ids,
            species,
            output_type="all",
        )

        assert map(lambda x: type(x) == StaticFeatureTimeSpecies, static_species_time)

        expected_size = (
            len(point_ids_valid(source))
            * len(features)
            * len(species)
            * ((end_datetime - start_datetime).total_seconds() / (60.0 * 60.0))
        )

        assert len(static_species_time) == expected_size

    def test_select_static_missing_id(
        self, model_data, valid_full_config_dataset, point_ids_valid
    ):
        """
        Test that we can cross join ModelData.select_static_features
        with a range of datetimes and species
        """
        source = Source.laqn
        species = [Species.NO2]

        # Id's from config file and another UUID
        config_ids = valid_full_config_dataset.train_interest_points[source] + [
            str(uuid.uuid4())
        ]
        start_datetime = valid_full_config_dataset.train_start_date
        end_datetime = valid_full_config_dataset.train_end_date

        features = [FeatureNames.building_height, FeatureNames.grass]

        # Return Pydantic model types
        static_species_time = model_data.get_static_features(
            start_datetime,
            end_datetime,
            features,
            source,
            config_ids,
            species,
            output_type="all",
        )

        expected_size = len(config_ids) - 1 * len(features) * len(species) * (
            (end_datetime - start_datetime).total_seconds() / (60.0 * 60.0)
        )

        assert len(static_species_time) != expected_size

        # print(StaticFeatureTimeSpecies.from_orm(static_species_time[0]))


# ToDo: Refactor when ModelData class if refactored

# from cleanair.types import Species, TargetDict


# def test_training_dicts(model_data):
#     """Check the shape of all the numpy arrays are correct."""
#     # load the dicts from modeldata
#     training_data_dict = model_data.get_training_data_arrays(dropna=False)
#     x_train = training_data_dict["X"]
#     y_train = training_data_dict["Y"]

#     # checks for satellite
#     assert not model_data.config["include_satellite"] or "satellite" in x_train
#     assert not model_data.config["include_satellite"] or "satellite" in y_train

#     # checks that each pollutant has a key in y_train for each source
#     all_train_sources = (
#         model_data.config["train_sources"]
#         if not model_data.config["include_satellite"]
#         else model_data.config["train_sources"] + ["satellite"]
#     )
#     for source in all_train_sources:
#         # check all training sources exist in the dicts
#         assert source in x_train
#         assert source in y_train

#         # check the shape of x_train
#         if source == "satellite":
#             assert len(x_train[source].shape) == 3
#         else:
#             assert len(x_train[source].shape) == 2

#         # check y_train
#         for pollutant in model_data.config["species"]:
#             assert y_train[source][pollutant].shape[0] == x_train[source].shape[0]
#         validate_target(y_train[source])


# def test_pred_dict(model_data):
#     """
#     Check the test set is in the right format.
#     """
#     predict_data_dict = model_data.get_pred_data_arrays(dropna=False, return_y=True)
#     x_test = predict_data_dict["X"]
#     y_test = predict_data_dict["Y"]
#     assert "satellite" not in x_test

#     for source in model_data.config["pred_sources"]:
#         # check x test
#         assert source in x_test
#         assert len(x_test[source].shape) == 2
#         assert x_test[source].shape[1] == len(model_data.config["x_names"])

#         # check y test
#         assert source in y_test
#         assert len(model_data.config["species"]) == len(y_test[source])
#         validate_target(y_test[source])


# def validate_target(Y: TargetDict) -> bool:
#     """Check the shapes and structure of Y."""
#     for pollutant, array in Y.items():
#         print(pollutant)
#         assert Species.has_key(pollutant)
#         assert len(array.shape) == 2
#         assert array.shape[1] == 1
