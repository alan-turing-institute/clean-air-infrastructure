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
from itertools import product
from dateutil.parser import isoparse
from dateutil import rrule
from datetime import timedelta, datetime
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


@pytest.fixture()
def point_ids_invalid(meta_within_london_closed):
    "A sample of invalid interest points (i.e. they are within london by closed"

    def _point_ids_valid(source):
        return [i.id for i in meta_within_london_closed if i.source == source]

    return _point_ids_valid


@pytest.fixture()
def lookup_sensor_reading(
    meta_records,
    laqn_site_records,
    laqn_reading_records,
    aqe_site_records,
    aqe_reading_records,
):
    def _lookup_sensor_reading(point_id, measurement_start_utc, species):

        sources = list(filter(lambda x: x.id == point_id, meta_records))
        if len(sources) != 1:
            raise ValueError("Got more than one source at lookup")
        source = sources[0].source

        if source == Source.laqn.value:

            site_records = laqn_site_records
            reading_records = laqn_reading_records

        elif source == Source.aqe.value:

            site_records = aqe_site_records
            reading_records = aqe_reading_records

        source_record = list(filter(lambda x: x.point_id == point_id, site_records))[0]

        record = list(
            filter(
                lambda x: (
                    (source_record.site_code == x.site_code)
                    and (measurement_start_utc == x.measurement_start_utc)
                    and (species.value == x.species_code)
                ),
                reading_records,
            )
        )

        if len(record) != 1:
            raise ValueError("Failed to get record value")

        return record[0].value

    return _lookup_sensor_reading


class TestModelData:
    def test_setup(self, fake_cleanair_dataset):
        """Insert test data"""

        pass

    def test_select_static_features(self, model_data, point_ids_valid):

        point_id = [str(point_ids_valid(Source.laqn)[0])]
        source = Source.laqn
        features = [FeatureNames.building_height, FeatureNames.grass]
        # Get a single valid point id
        dat = model_data.select_static_features(
            point_id, features, source, output_type="all",
        )

        assert len(dat) == len(features)
        assert all([point_id[0] == str(i.point_id) for i in dat])
        assert {i.value for i in features} == {i.feature_name for i in dat}

    def test_select_static_features_invalid(self, model_data):
        """When we request a point ID not in the database we should
            get empty features back. However, if we validate with
            a pydantic model it should raise a runtime error
        """
        point_id = [str(uuid.uuid4())]

        source = Source.laqn
        features = [FeatureNames.building_height, FeatureNames.grass]

        # Get a single valid point id
        dat = model_data.select_static_features(
            point_id, features, source, output_type="query",
        ).all()

        assert len(dat) == len(features)
        assert all([point_id[0] == str(i.point_id) for i in dat])
        assert {i.value for i in features} == {i.feature_name for i in dat}

        # But also not valid because point_id not in database,
        # so check we get an validation error.

        with pytest.raises(ValidationError):
            model_data.select_static_features(
                point_id, features, source, output_type="all",
            )

    @pytest.mark.parametrize("source", [Source.laqn, Source.aqe, Source.satellite])
    def test_select_static_features_config(
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
            config_ids,
            [FeatureNames.building_height, FeatureNames.grass],
            source,
            output_type="all",
        )

        returned_static_features = {i.point_id for i in dat}

        # assert set(config_ids) == set(point_ids_valid(source))

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
        static_species_tuples = [
            (
                i.point_id,
                i.feature_name,
                i.species_code,
                i.measurement_start_utc.replace(tzinfo=None),
            )
            for i in static_species_time
        ]

        expected_values = list(
            product(
                [uuid.UUID(id) for id in config_ids],
                features,
                species,
                rrule.rrule(
                    freq=rrule.HOURLY,
                    dtstart=start_datetime,
                    until=end_datetime - timedelta(hours=1),
                ),
            )
        )

        assert sorted(expected_values) == sorted(static_species_tuples)

    # @pytest.mark.parametrize("source", [Source.laqn, Source.aqe, Source.satellite])
    # @pytest.mark.parametrize(
    #     "species", [[Species.NO2], [Species.PM10], [Species.NO2, Species.PM10]]
    # )
    @pytest.mark.parametrize("source", [Source.laqn, Source.aqe])
    @pytest.mark.parametrize("species", [[Species.NO2]])
    def test_get_training_data_inputs(
        self,
        model_data,
        valid_full_config_dataset,
        point_ids_valid,
        source,
        species,
        lookup_sensor_reading,
    ):

        # Id's from config file
        config_ids = valid_full_config_dataset.train_interest_points[source]
        start_datetime = valid_full_config_dataset.train_start_date
        end_datetime = valid_full_config_dataset.train_end_date

        features = [FeatureNames.building_height, FeatureNames.grass]

        data = model_data.get_training_data_inputs(
            start_datetime,
            end_datetime,
            species,
            config_ids,
            features,
            source,
            output_type="all",
        )

        assert all(
            map(
                lambda v: lookup_sensor_reading(
                    v.point_id,
                    v.measurement_start_utc.replace(tzinfo=None),
                    v.species_code,
                )
                == v.value,
                data,
            )
        )


#     # def test_select_static_missing_id(
#     #     self, model_data, valid_full_config_dataset, point_ids_valid
#     # ):
#     #     """
#     #     Test that we can cross join ModelData.select_static_features
#     #     with a range of datetimes and species
#     #     """
#     #     source = Source.laqn
#     #     species = [Species.NO2]

#     #     # Id's from config file and another UUID
#     #     extra_id = str(uuid.uuid4())

#     #     config_ids = valid_full_config_dataset.train_interest_points[source] + [
#     #         extra_id
#     #     ]
#     #     start_datetime = valid_full_config_dataset.train_start_date
#     #     end_datetime = valid_full_config_dataset.train_end_date

#     #     features = [FeatureNames.building_height, FeatureNames.grass]

#     #     # Return Pydantic model types
#     #     static_species_time = model_data.get_static_features(
#     #         start_datetime,
#     #         end_datetime,
#     #         features,
#     #         source,
#     #         config_ids,
#     #         species,
#     #         output_type="all",
#     #     )

#     # print(list(filter(lambda x: x.point_id == extra_id, static_species_time)))
#     # expected_size = (
#     #     len(config_ids)
#     #     * len(features)
#     #     * len(species)
#     #     * ((end_datetime - start_datetime).total_seconds() / (60.0 * 60.0))
#     # )

#     # assert len(static_species_time) == expected_size

#     # print(StaticFeatureTimeSpecies.from_orm(static_species_time[0]))


# # ToDo: Refactor when ModelData class if refactored

# # from cleanair.types import Species, TargetDict


# # def test_training_dicts(model_data):
# #     """Check the shape of all the numpy arrays are correct."""
# #     # load the dicts from modeldata
# #     training_data_dict = model_data.get_training_data_arrays(dropna=False)
# #     x_train = training_data_dict["X"]
# #     y_train = training_data_dict["Y"]

# #     # checks for satellite
# #     assert not model_data.config["include_satellite"] or "satellite" in x_train
# #     assert not model_data.config["include_satellite"] or "satellite" in y_train

# #     # checks that each pollutant has a key in y_train for each source
# #     all_train_sources = (
# #         model_data.config["train_sources"]
# #         if not model_data.config["include_satellite"]
# #         else model_data.config["train_sources"] + ["satellite"]
# #     )
# #     for source in all_train_sources:
# #         # check all training sources exist in the dicts
# #         assert source in x_train
# #         assert source in y_train

# #         # check the shape of x_train
# #         if source == "satellite":
# #             assert len(x_train[source].shape) == 3
# #         else:
# #             assert len(x_train[source].shape) == 2

# #         # check y_train
# #         for pollutant in model_data.config["species"]:
# #             assert y_train[source][pollutant].shape[0] == x_train[source].shape[0]
# #         validate_target(y_train[source])


# # def test_pred_dict(model_data):
# #     """
# #     Check the test set is in the right format.
# #     """
# #     predict_data_dict = model_data.get_pred_data_arrays(dropna=False, return_y=True)
# #     x_test = predict_data_dict["X"]
# #     y_test = predict_data_dict["Y"]
# #     assert "satellite" not in x_test

# #     for source in model_data.config["pred_sources"]:
# #         # check x test
# #         assert source in x_test
# #         assert len(x_test[source].shape) == 2
# #         assert x_test[source].shape[1] == len(model_data.config["x_names"])

# #         # check y test
# #         assert source in y_test
# #         assert len(model_data.config["species"]) == len(y_test[source])
# #         validate_target(y_test[source])


# # def validate_target(Y: TargetDict) -> bool:
# #     """Check the shapes and structure of Y."""
# #     for pollutant, array in Y.items():
# #         print(pollutant)
# #         assert Species.has_key(pollutant)
# #         assert len(array.shape) == 2
# #         assert array.shape[1] == 1
