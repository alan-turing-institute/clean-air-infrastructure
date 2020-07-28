"""
Tests related to the ModelConfig class
"""
import pytest
from enum import Enum
from dateutil.parser import isoparse
from datetime import timedelta
from pydantic import ValidationError
from cleanair.models import ModelConfig
from cleanair.types.dataset_types import BaseConfig, FullConfig

from cleanair.types import Species, Source, FeatureNames, FeatureBufferSize
from cleanair.databases import DBWriter
from cleanair.databases.tables import MetaPoint
from cleanair.exceptions import MissingFeatureError, MissingSourceError


@pytest.fixture(scope="class")
def model_config(secretfile, connection_class):

    return ModelConfig(secretfile=secretfile, connection=connection_class)


@pytest.fixture()
def valid_config(dataset_start_date, dataset_end_date):

    return BaseConfig(
        **{
            "train_start_date": dataset_start_date,
            "train_end_date": dataset_end_date,
            "pred_start_date": dataset_end_date,
            "pred_end_date": dataset_end_date + timedelta(days=2),
            "include_prediction_y": False,
            "train_sources": ["laqn", "satellite"],
            "pred_sources": ["satellite", "laqn", "hexgrid"],
            "train_interest_points": {"laqn": "all", "satellite": "all"},
            "pred_interest_points": {
                "satellite": "all",
                "laqn": "all",
                "hexgrid": "all",
            },
            "species": ["NO2"],
            "features": [
                "total_road_length",
                "total_a_road_length",
                "total_a_road_primary_length",
                "total_b_road_length",
                "grass",
                "building_height",
                "water",
                "park",
                "max_canyon_narrowest",
                "max_canyon_ratio",
            ],
            "buffer_sizes": ["1000", "500"],
            "norm_by": "laqn",
            "model_type": "svgp",
        }
    )


class TestModelConfig:
    def test_setup(self, fake_cleanair_dataset):
        """Insert test data"""

        pass

    def test_generate_config(self, model_config):

        try:
            model_config.generate_data_config(
                "2020-01-01",
                48,
                48,
                [Source.laqn, Source.aqe, Source.satellite],
                [Source.laqn, Source.hexgrid],
                [Species.NO2],
                [i.value for i in FeatureNames],
                [i.value for i in FeatureBufferSize],
                Source.laqn,
                "svgp",
            )
        except ValueError as e:
            pytest.fail(e)

    @pytest.mark.parametrize(
        "trainupto,train_sources,pred_sources,species,features,buffer_sizes,norm_by,model_type",
        [
            # Uses an invalid source
            pytest.param(
                "2020-01-01",
                [Source.laqn, Source.aqe, Source.satellite],
                [Source.laqn, Source.hexgrid],
                [Species.NO2],
                [i.value for i in FeatureNames],
                [i.value for i in FeatureBufferSize],
                "not_a_source",
                "svgp",
            ),
            # Species rather than source in pred source
            pytest.param(
                "2020-01-01",
                [Source.laqn, Source.aqe, Source.satellite],
                [Source.laqn, Species.NO2],
                [Species.NO2],
                [i.value for i in FeatureNames],
                [i.value for i in FeatureBufferSize],
                Source.laqn,
                "svgp",
            ),
        ],
    )
    def test_generate_config_invalid(
        self,
        model_config,
        trainupto,
        train_sources,
        pred_sources,
        species,
        features,
        buffer_sizes,
        norm_by,
        model_type,
    ):
        "Test parameter validation"

        with pytest.raises(ValidationError):
            model_config.generate_data_config(
                trainupto,
                48,
                48,
                train_sources,
                pred_sources,
                species,
                features,
                buffer_sizes,
                norm_by,
                model_type,
            )

    def test_validation_static_features(
        self, valid_config, model_config, static_feature_records
    ):
        """Check static features raise error when missing"""

        # All static features in database
        assert {i.feature_name for i in static_feature_records} == set(
            model_config.get_available_static_features(output_type="list")
        )

        # Check feature availability doesn't raise an error
        try:
            model_config.check_features_available(
                valid_config.features,
                valid_config.train_start_date,
                valid_config.pred_end_date,
            )
        except Exception:
            pytest.fail("Unexpected error")

        class FakeFeature(str, Enum):

            fake_feature = "fake_feature"

        # Check error raised when features missing
        with pytest.raises(MissingFeatureError):
            model_config.check_features_available(
                [FakeFeature.fake_feature],
                valid_config.train_start_date,
                valid_config.pred_end_date,
            )

    def test_validation_source_available(
        self, valid_config, model_config, static_feature_records
    ):

        # All sources in database
        assert {i.feature_source.value for i in static_feature_records}.issubset(
            set(model_config.get_available_sources(output_type="list"))
        )

        # Check source availability doesn't raise an error
        try:
            model_config.check_sources_available(valid_config.train_sources)
        except Exception:
            pytest.fail("Unexpected error")
        try:
            model_config.check_sources_available(valid_config.pred_sources)
        except Exception:
            pytest.fail("Unexpected error")

        class FakeSource(str, Enum):
            fake_source = "fake_source"

        # Check error raised when features missing
        with pytest.raises(MissingSourceError):
            model_config.check_sources_available([FakeSource.fake_source])

    def test_validate_config(self, valid_config, model_config):
        "Check all validations pass"

        try:
            model_config.validate_config(valid_config)
        except Exception:
            pytest.raises("Unexpected error")

    @pytest.mark.parametrize(
        "interest_points_name", [("train_interest_points"), ("pred_interest_points")],
    )
    def test_get_interest_point_ids(
        self, valid_config, model_config, interest_points_name
    ):
        "Check we get all interest points"

        interest_points = getattr(valid_config, interest_points_name)
        sources = interest_points.keys()

        all_interest_points = model_config.get_interest_point_ids(interest_points)

        for source in sources:

            with model_config.dbcnxn.open_session() as session:

                meta_ids = (
                    session.query(MetaPoint.id).filter(MetaPoint.source == source).all()
                )

            meta_ids = [str(i.id) for i in meta_ids]
            interest_ids = all_interest_points[source]

            assert set(meta_ids) == set(interest_ids)

    # def test_full_config(self, valid_config, model_config, meta_records):

    #     full_config = model_config.generate_full_config(valid_config)

    #     sources = full_config.train_interest_points.keys()

    #     for src in sources:

    #         assert full_config.train_interest_points[src] == [
    #             i.id for i in meta_records if i.source == src
    #         ]


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
