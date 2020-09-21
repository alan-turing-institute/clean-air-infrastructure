"""
Tests related to the ModelConfig class
"""
import pytest
from enum import Enum
from dateutil.parser import isoparse
from datetime import timedelta
from pydantic import ValidationError
from cleanair.models import ModelConfig
from cleanair.types.dataset_types import DataConfig, FullDataConfig

from cleanair.types import Species, Source, FeatureNames, FeatureBufferSize
from cleanair.databases import DBWriter
from cleanair.databases.tables import MetaPoint
from cleanair.exceptions import MissingFeatureError, MissingSourceError


class TestDataConfig:
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
            )
        except ValueError as e:
            pytest.fail(e)

    @pytest.mark.parametrize(
        "trainupto,train_sources,pred_sources,species,features,buffer_sizes,norm_by",
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

    def test_get_interest_point_ids_open_laqn(
        self, valid_config, model_config, laqn_sites_open
    ):
        "Check we get all interest points"

        # Check we get all open sites and not any closed sites
        laqn_point_ids = {str(rec.point_id) for rec in laqn_sites_open}
        assert laqn_point_ids == {
            str(i)
            for i in model_config.get_available_interest_points(
                Source.laqn, within_london_only=False, output_type="list"
            )
        }

    def test_get_interest_point_ids_open_laqn_within_london(
        self, valid_config, model_config, meta_within_london
    ):
        "Check we get all interest points"

        # Check we get all open sites and not any closed sites
        laqn_point_ids_in_london = {
            str(rec.id) for rec in meta_within_london if rec.source == Source.laqn
        }

        assert laqn_point_ids_in_london == {
            str(i)
            for i in model_config.get_available_interest_points(
                Source.laqn, within_london_only=True, output_type="list"
            )
        }

    def test_get_box_ids_within_london(self, model_config, satellite_box_records):
        """Check we only get box ids which intersect with the London Boundary
        
        We know two are outside the London boundary in the test set"""

        n_outside_london = 2
        assert (
            len(satellite_box_records) - n_outside_london
            == model_config.get_satellite_box_in_boundary().count()
        )

    def test_get_satellite_point_ids(self, model_config):

        satellite_interest_points = model_config.get_satellite_interest_points_in_boundary(
            output_type="list"
        )

        satellite_interest_points_available = model_config.get_available_interest_points(
            Source.satellite, within_london_only=False, output_type="list"
        )

        assert {str(i) for i in satellite_interest_points} == set(
            satellite_interest_points_available
        )

        # Check we filter correctly
        satellite_interest_points_available_in_london = model_config.get_available_interest_points(
            Source.satellite, within_london_only=True, output_type="list"
        )

        # ToDo: Come up with a better test than this!
        assert len(satellite_interest_points_available_in_london) < len(
            satellite_interest_points_available
        )

        # Now use the function that calls the get_available_interest_points
        satellite_interest_points_available_in_london2 = model_config.get_interest_point_ids(
            {Source.satellite: "all"}
        )[
            Source.satellite
        ]

        assert set(satellite_interest_points_available_in_london2) == set(
            satellite_interest_points_available
        )

    def test_generate_full_config(self, valid_config, model_config, meta_within_london):
        """Test full config doesnt raise any validation errors"""
        # ToDo: Write a full config file for the test set to verify
        try:
            full_config = model_config.generate_full_config(valid_config)

            for source in [Source.laqn, Source.aqe]:
                full_config.train_interest_points[source] == [
                    i for i in meta_within_london if i.source == source.value
                ]

        except ValidationError:
            pytest.raises("Full config failed")
